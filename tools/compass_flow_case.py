"""Shared synthetic project for public Compass-flow tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'check/tokens-qa/scripts/tokens_qa.py'
CONTEXT = ROOT / 'tools/repo_context.py'


class CompassFlowCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'request.txt').write_text('Synthetic fixture: deliver one file')
        (self.root / 'proof.txt').write_text('Synthetic passing test evidence')
        (self.root / 'manifest.json').write_text(json.dumps({
            'artifacts': [{'role': 'proof', 'path': 'proof.txt'}]}))
        (self.root / 'gates.json').write_text(json.dumps({'l2': {'status': 'pass',
            'name': 'synthetic acceptance check', 'observer': 'fixture',
            'observed_at': '2026-09-05T00:00:00Z', 'artifacts': ['proof.txt']}}))
        self.roadmap()

    def roadmap(self, state='IN-PROGRESS', shot=''):
        (self.root / 'ROADMAP.md').write_text(
            '| ID | State | Item | Workstream | Depends on | Scope | Proof | Shot |\n'
            '| --- | --- | --- | --- | --- | --- | --- | --- |\n'
            f'| F-1 | {state} | First | default | | proof.txt | test | {shot} |\n'
            '| F-2 | TODO | Next | default | F-1 | next.txt | test | |\n')

    def run_command(self, script, *args, code=0):
        result = subprocess.run([sys.executable, str(script), *map(str, args)],
                                cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def qa(self, verb, *args, code=0):
        return self.run_command(QA, verb, *args, '--json', code=code)['result']

    def next(self):
        return self.run_command(CONTEXT, '--root', self.root, '--json', 'next')

    def record(self):
        return self.qa('record', 'fixture', '--project-root', self.root,
                       '--item-id', 'F-1', '--request', self.root / 'request.txt',
                       '--output-manifest', self.root / 'manifest.json',
                       '--gates', self.root / 'gates.json')['path']
