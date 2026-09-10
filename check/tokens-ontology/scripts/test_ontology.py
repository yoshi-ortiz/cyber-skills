"""Public manifest safety and stale-index regression checks."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ontology


class OntologyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'src').mkdir()
        (self.root / 'src' / 'auth.py').write_text('authorize = True\n' * 90)

    def test_bounded_scan_and_exclusions(self):
        (self.root / 'src' / '.env').write_text('SECRET=private')
        (self.root / 'src' / 'credentials.json').write_text('{}')
        (self.root / 'src' / 'binary.py').write_bytes(b'\0binary')
        (self.root / 'outside.md').write_text('unrelated')
        value = ontology.manifest(self.root, ['src'])
        self.assertEqual([(c['start'], c['end']) for c in value['chunks']],
                         [(1, 80), (81, 90)])
        self.assertEqual({c['path'] for c in value['chunks']}, {'src/auth.py'})
        self.assertEqual(len(value['skipped']), 3)
        ontology.validate(value)

    def test_stale_and_tampered_manifest_refused(self):
        value = ontology.manifest(self.root, ['src'])
        value['chunks'][0]['text'] = 'made up'
        with self.assertRaisesRegex(ValueError, 'identity'):
            ontology.validate(value)
        value = ontology.manifest(self.root, ['src'])
        (self.root / 'src' / 'auth.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'stale'):
            ontology.validate(value)

    def test_symlink_and_escape_excluded(self):
        with tempfile.TemporaryDirectory() as outside:
            secret = Path(outside) / 'private.py'
            secret.write_text('private')
            (self.root / 'src' / 'link.py').symlink_to(secret)
            value = ontology.manifest(self.root, ['src'])
            self.assertNotIn('src/link.py', [c['path'] for c in value['chunks']])
            with self.assertRaisesRegex(ValueError, 'escapes'):
                ontology.manifest(self.root, [outside])

    def test_git_ignored_source_excluded(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('src/ignored.py\n')
        (self.root / 'src' / 'ignored.py').write_text('private')
        value = ontology.manifest(self.root, ['src'])
        self.assertNotIn('src/ignored.py', [c['path'] for c in value['chunks']])

    def test_cli_exclusive_output_and_json(self):
        output = self.root / 'manifest.json'
        args = ['manifest', '--root', str(self.root), '--include', 'src',
                '--out', str(output)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ontology.main(args), 0)
            original = output.read_bytes()
            self.assertEqual(ontology.main(args), 1)
        self.assertEqual(output.read_bytes(), original)
        ontology.validate(json.loads(original))

    def test_invalid_embeddings_refused_before_database(self):
        value = ontology.manifest(self.root, ['src'])
        value.update(embedding={'dimensions': 2}, vectors=[[1, 2], [float('nan'), 1]])
        with patch.object(ontology, 'connect') as connection:
            with self.assertRaisesRegex(ValueError, 'invalid vector'):
                ontology.index(value)
            connection.assert_not_called()
        value['vectors'] = [[0, 0], [1, 1]]
        with self.assertRaisesRegex(ValueError, 'nonzero'):
            ontology.validate_vectors(value)

    def test_pgvector_index_uses_one_transaction(self):
        class Connection:
            def __init__(self):
                self.calls = []

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def execute(self, sql, params=None):
                self.calls.append((sql, params))

        value = ontology.manifest(self.root, ['src'])
        value.update(embedding={'model_path': '/model', 'model_hash': 'hash',
                                'dimensions': 2},
                     vectors=[[1, 0], [0, 1]])
        connection = Connection()
        with patch.object(ontology, 'connect', return_value=connection):
            result = ontology.index(value)
        self.assertEqual(result['chunks'], 2)
        self.assertEqual(len(connection.calls), 4)
        self.assertIn('CREATE EXTENSION IF NOT EXISTS vector', connection.calls[0][0])
        self.assertIn('%s::vector', connection.calls[-1][0])

    def test_newlines_preserved(self):
        (self.root / 'src' / 'auth.py').write_bytes(b'hello\r\nworld\r\n')
        ontology.validate(ontology.manifest(self.root, ['src']))


if __name__ == '__main__':
    unittest.main()
