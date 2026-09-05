"""Public command regression: synthetic feedback never touches real project state."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'check/tokens-qa/scripts/tokens_qa.py'
CONTEXT = ROOT / 'tools/repo_context.py'


class CompassFlow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'request.txt').write_text('Synthetic fixture: deliver one file')
        (self.root / 'proof.txt').write_text('Synthetic passing test evidence')
        (self.root / 'manifest.json').write_text(json.dumps({
            'artifacts': [{'role': 'proof', 'path': 'proof.txt'}]}))
        (self.root / 'gates.json').write_text(json.dumps({'l2': {'status': 'pass'}}))
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

    def test_feedback_proof_and_next_feature(self):
        self.assertEqual(self.next()['item_id'], 'F-1')
        shot = self.record()
        self.assertEqual(self.next()['next_action'], 'await-feedback')
        self.qa('feedback', shot, '--status', 'rejected', '--correction', 'Fix the result')
        result = self.next()
        self.assertEqual(result['next_action'], 'apply-correction')
        self.assertEqual(result['observations']['latest']['correction'], 'Fix the result')
        shot = self.record()
        self.qa('feedback', shot, '--status', 'accepted')
        self.assertEqual(self.next()['next_action'], 'close-item')
        self.roadmap('DONE', shot)
        self.run_command(CONTEXT, '--root', self.root, 'check')
        self.assertEqual(self.next()['item_id'], 'F-2')
        (self.root / 'proof.txt').write_text('tampered')
        self.run_command(CONTEXT, '--root', self.root, 'check', code=1)

    def test_unknown_cost_and_premature_done(self):
        shot = self.record()
        history = self.qa('history', '--project-root', self.root, '--item-id', 'F-1')
        self.assertIsNone(history['totals_by_profile']['unknown']['input'])
        self.roadmap('DONE', shot)
        self.run_command(CONTEXT, '--root', self.root, 'check', code=1)

    def test_outside_artifact_is_refused(self):
        (self.root / 'manifest.json').write_text(json.dumps({
            'artifacts': [{'role': 'proof', 'path': str(__file__)}]}))
        self.run_command(QA, 'record', 'fixture', '--project-root', self.root,
                         '--item-id', 'F-1', '--request', self.root / 'request.txt',
                         '--output-manifest', self.root / 'manifest.json', '--json', code=2)

    def test_budget_unknown_and_exhausted(self):
        roadmap = self.root / 'ROADMAP.md'
        roadmap.write_text('| ID | State | Item | Workstream | Scope | Proof | Budget tokens |\n'
                           '| --- | --- | --- | --- | --- | --- | --- |\n'
                           '| F-1 | IN-PROGRESS | First | default | proof.txt | test | 0 |\n')
        self.assertEqual(self.next()['next_action'], 'budget-exhausted')
        self.record()
        shot = self.next()['observations']['latest']['path']
        self.qa('feedback', shot, '--status', 'rejected')
        self.assertEqual(self.next()['next_action'], 'resolve-budget')

    def test_scope_prefix_is_not_a_directory(self):
        result = self.qa('record', 'fixture', '--project-root', self.root,
                         '--item-id', 'F-1', '--request', self.root / 'request.txt',
                         '--inline', 'fixture', '--changed', 'src-other/a,src/../outside',
                         '--within', 'src')
        self.assertIn('scope_breach', result['findings'])


if __name__ == '__main__':
    unittest.main()
