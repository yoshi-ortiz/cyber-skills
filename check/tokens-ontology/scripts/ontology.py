#!/usr/bin/env python3
"""Bounded repository manifests, pgvector retrieval and advisory EVoC maps."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

SKIP = {'.git', '.audit', '.scratch', 'node_modules', '.venv', 'venv',
        'dist', '__pycache__'}
TEXT = {'.md', '.txt', '.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.toml',
        '.yaml', '.yml', '.rs', '.go', '.java', '.swift', '.css', '.html', '.sql',
        '.c', '.h', '.cpp', '.sh', '.rb'}
MAX_BYTES = 256_000


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fingerprint(value: dict) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def save(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def manifest(root: Path, includes: list[str]) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('root must be a directory')
    scopes = []
    for scope in includes:
        resolved = (root / scope).resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise ValueError('include escapes project root')
        scopes.append(resolved)
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z',
                             '--cached', '--others', '--exclude-standard'],
                            capture_output=True, check=False)
    if result.returncode == 0:
        paths = [root / os.fsdecode(p) for p in result.stdout.split(b'\0') if p]
    else:
        paths = []
        for scope in scopes:
            if scope.is_file():
                paths.append(scope)
            else:
                for directory, dirs, files in os.walk(scope, followlinks=False):
                    dirs[:] = [d for d in dirs if d not in SKIP and
                               not (Path(directory) / d).is_symlink()]
                    paths.extend(Path(directory) / f for f in files)
    chunks, skipped = [], []
    for path in sorted(set(paths)):
        relative = path.relative_to(root)
        resolved = path.resolve()
        if not any(resolved == s or resolved.is_relative_to(s) for s in scopes):
            continue
        reason = None
        if not resolved.is_relative_to(root) or any(
                part.is_symlink() for part in [path, *path.parents] if part != root):
            reason = 'symlink'
        elif any(part in SKIP for part in relative.parts):
            reason = 'generated or private directory'
        elif path.name.startswith('.env') or any(
                word in path.name.lower() for word in ('secret', 'credential')):
            reason = 'sensitive filename'
        elif path.suffix.lower() not in TEXT:
            reason = 'unsupported file type'
        elif not path.is_file():
            reason = 'missing file'
        elif path.stat().st_size > MAX_BYTES:
            reason = 'oversize'
        if reason:
            skipped.append({'path': relative.as_posix(), 'reason': reason})
            continue
        raw = path.read_bytes()
        try:
            content = raw.decode('utf-8')
            if '\0' in content:
                raise UnicodeError('binary')
        except UnicodeError:
            skipped.append({'path': relative.as_posix(), 'reason': 'non-text'})
            continue
        lines = content.splitlines(keepends=True)
        for offset in range(0, len(lines), 80):
            text = ''.join(lines[offset:offset + 80])
            chunks.append({'path': relative.as_posix(), 'start': offset + 1,
                           'end': min(offset + 80, len(lines)),
                           'file_hash': digest(raw), 'text': text})
    value = {'version': 1, 'root': str(root), 'includes': includes,
             'chunks': chunks, 'skipped': skipped}
    value['snapshot'] = fingerprint(value)
    return value


def validate(value: dict) -> None:
    if value.get('version') != 1:
        raise ValueError('unsupported manifest version')
    source = {k: v for k, v in value.items()
              if k not in {'snapshot', 'embedding', 'vectors'}}
    if fingerprint(source) != value.get('snapshot'):
        raise ValueError('manifest identity mismatch')
    root = Path(value['root']).resolve(strict=True)
    checked = set()
    for chunk in value['chunks']:
        path = root / chunk['path']
        if not path.resolve().is_relative_to(root) or any(
                parent.is_symlink() for parent in [path, *path.parents] if parent != root):
            raise ValueError('chunk path escapes root or is a symlink')
        if chunk['path'] not in checked:
            if digest(path.read_bytes()) != chunk['file_hash']:
                raise ValueError(f"stale manifest: {chunk['path']}")
            checked.add(chunk['path'])
        lines = path.read_bytes().decode('utf-8').splitlines(keepends=True)
        if ''.join(lines[chunk['start'] - 1:chunk['end']]) != chunk['text']:
            raise ValueError('chunk content differs from source')


def validate_vectors(value: dict) -> None:
    vectors = value['vectors']
    dim = value['embedding']['dimensions']
    if type(dim) is not int or not 1 <= dim <= 16000:
        raise ValueError('invalid vector dimension')
    if len(vectors) != len(value['chunks']) or not vectors:
        raise ValueError('embedding count must match nonempty chunks')
    for row in vectors:
        if len(row) != dim or any(type(x) not in (int, float) or
                                  not math.isfinite(x) for x in row):
            raise ValueError('invalid vector values or dimension')
        if not any(row):
            raise ValueError('cosine search requires nonzero vectors')


def embed(value: dict, model_path: str) -> dict:
    from model2vec import StaticModel
    validate(value)
    path = Path(model_path).resolve(strict=True)
    if not path.is_dir():
        raise ValueError('model must be a local model directory')
    files = sorted(p for p in path.rglob('*') if p.is_file())
    model_hash = fingerprint({str(p.relative_to(path)): digest(p.read_bytes())
                              for p in files})
    model = StaticModel.from_pretrained(str(path))
    vectors = model.encode([c['text'] for c in value['chunks']]).tolist()
    result = dict(value, embedding={'model_path': str(path), 'model_hash': model_hash,
                                   'dimensions': len(vectors[0]) if vectors else 0},
                  vectors=vectors)
    validate_vectors(result)
    return result


def connect():
    import psycopg
    # Use standard PG* environment variables; credentials never enter artifacts.
    return psycopg.connect('')


def index(value: dict) -> dict:
    validate(value)
    validate_vectors(value)
    identity = fingerprint({'snapshot': value['snapshot'], 'embedding': value['embedding']})
    with connect() as conn:
        conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        conn.execute('''CREATE TABLE IF NOT EXISTS tokens_context (
          index_id text NOT NULL, chunk_id integer NOT NULL,
          path text NOT NULL, line_start integer NOT NULL, line_end integer NOT NULL,
          content text NOT NULL, embedding vector NOT NULL,
          PRIMARY KEY (index_id, chunk_id))''')
        for number, (chunk, vector) in enumerate(zip(value['chunks'], value['vectors'])):
            conn.execute('''INSERT INTO tokens_context VALUES
              (%s, %s, %s, %s, %s, %s, %s::vector)
              ON CONFLICT (index_id, chunk_id) DO UPDATE SET
              path=EXCLUDED.path, line_start=EXCLUDED.line_start,
              line_end=EXCLUDED.line_end, content=EXCLUDED.content,
              embedding=EXCLUDED.embedding''',
                         (identity, number, chunk['path'], chunk['start'], chunk['end'],
                          chunk['text'], json.dumps(vector)))
    return {'index_id': identity, 'chunks': len(value['chunks']),
            'snapshot': value['snapshot']}


def search(value: dict, query: str, limit: int) -> dict:
    validate(value)
    validate_vectors(value)
    # Reuse the exact local model; verify identity before issuing a query.
    from model2vec import StaticModel
    model_path = Path(value['embedding']['model_path'])
    files = sorted(p for p in model_path.rglob('*') if p.is_file())
    actual = fingerprint({str(p.relative_to(model_path)): digest(p.read_bytes()) for p in files})
    if actual != value['embedding']['model_hash']:
        raise ValueError('embedding model changed; rebuild the index')
    model = StaticModel.from_pretrained(str(model_path))
    vector = model.encode([query]).tolist()[0]
    validate_vectors(dict(value, chunks=[{}], vectors=[vector]))
    identity = fingerprint({'snapshot': value['snapshot'], 'embedding': value['embedding']})
    with connect() as conn:
        rows = conn.execute('''SELECT path, line_start, line_end, content,
          embedding <=> %s::vector AS distance FROM tokens_context
          WHERE index_id = %s ORDER BY distance, chunk_id LIMIT %s''',
                            (json.dumps(vector), identity, limit)).fetchall()
    return {'index_id': identity, 'query': query, 'results': [dict(
        zip(('path', 'start', 'end', 'text', 'distance'), row)) for row in rows]}


def explore(value: dict, seed: int) -> dict:
    validate(value)
    validate_vectors(value)
    if len(value['chunks']) < 16:
        raise ValueError('EVoC exploration requires at least 16 chunks; use retrieval')
    import numpy as np
    from evoc import EVoC
    from importlib.metadata import version
    clusterer = EVoC(random_state=seed)
    labels = clusterer.fit_predict(np.asarray(value['vectors'], dtype=np.float32))
    return {'version': 1, 'snapshot': value['snapshot'], 'embedding': value['embedding'],
            'seed': seed, 'parameters': {'random_state': seed},
            'versions': {'evoc': version('evoc'), 'numpy': version('numpy')},
            'purpose': 'advisory similarity map, not dependency or quality proof',
            'entries': [dict(path=c['path'], start=c['start'], end=c['end'],
                             cluster=int(label)) for c, label in zip(value['chunks'], labels)],
            'layers': [layer.tolist() for layer in clusterer.cluster_layers_]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    scan = commands.add_parser('manifest')
    scan.add_argument('--root', type=Path, required=True)
    scan.add_argument('--include', action='append', required=True)
    scan.add_argument('--out', type=Path, required=True)
    for verb in ('embed', 'index', 'search', 'explore'):
        sub = commands.add_parser(verb)
        sub.add_argument('--manifest', type=Path, required=True)
        if verb in ('embed', 'explore'):
            sub.add_argument('--out', type=Path, required=True)
        if verb == 'embed':
            sub.add_argument('--model', required=True, help='local model2vec model directory')
        if verb == 'search':
            sub.add_argument('--query', required=True)
            sub.add_argument('--limit', type=int, default=5)
        if verb == 'explore':
            sub.add_argument('--seed', type=int, default=42)
    args = parser.parse_args(argv)
    try:
        if args.command == 'manifest':
            result = manifest(args.root, args.include)
        else:
            value = json.loads(args.manifest.read_text())
            if args.command == 'embed':
                result = embed(value, args.model)
            elif args.command == 'index':
                result = index(value)
            elif args.command == 'search':
                if not 1 <= args.limit <= 100:
                    raise ValueError('limit must be between 1 and 100')
                result = search(value, args.query, args.limit)
            else:
                result = explore(value, args.seed)
        if getattr(args, 'out', None):
            save(args.out, result)
            print(json.dumps({'output': str(args.out), 'snapshot': result.get('snapshot')}))
        else:
            print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        # Database diagnostics can contain source text; expose the type only.
        message = str(error) if isinstance(error, (ValueError, FileExistsError, ImportError)) else type(error).__name__
        print(json.dumps({'error': message}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
