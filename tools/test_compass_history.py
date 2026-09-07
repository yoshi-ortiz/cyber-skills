"""Public Compass feedback-history and closure regressions."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

from compass_flow_case import CompassFlowCase, CONTEXT, QA, ROOT


class CompassHistory(CompassFlowCase):
    def test_incompatible_budget_blocks_execution_but_not_feedback(self):
        (self.root / 'ROADMAP.md').write_text(
            '| ID | State | Workstream | Scope | Proof | Budget tokens |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            '| F-1 | IN-PROGRESS | default | src/ | test | 100 |\n')
        for profile in ('model-a', 'model-b'):
            result = self.qa('record', 'fixture', '--project-root', self.root,
                             '--item-id', 'F-1', '--request', self.root / 'request.txt',
                             '--inline', 'result', '--tokens-input', '1', '--tokens-output', '1',
                             '--token-profile', profile)
        self.assertEqual(self.next()['next_action'], 'await-feedback')
        self.qa('feedback', result['path'], '--status', 'rejected')
        self.assertEqual(self.next()['next_action'], 'resolve-budget')

    def test_feedback_events_are_idempotent_and_survive_new_attempts(self):
        shot = self.record()
        args = ('--status', 'rejected', '--correction', 'Keep the heading',
                '--operation-id', 'reject-1')
        first = self.qa('feedback', shot, *args)
        self.assertEqual(self.qa('feedback', shot, *args)['revision'], first['revision'])
        second = self.record()
        history = self.qa('history', '--project-root', self.root, '--item-id', 'F-1')
        self.assertEqual(history['unresolved_corrections'][0]['correction'], 'Keep the heading')
        self.qa('feedback', second, '--status', 'accepted', '--resolve', first['event_id'],
                '--source-kind', 'user', '--source-ref', 'synthetic:user-turn',
                '--source-text', 'Resolved and accepted', '--observed-at', '2026-09-05T00:00:00Z')
        history = self.qa('history', '--project-root', self.root, '--item-id', 'F-1')
        self.assertEqual(history['unresolved_corrections'], [])
        self.assertEqual(history['feedback_events'], 2)

    def test_closure_requires_sourced_acceptance_and_detects_stale_revision(self):
        shot = self.record()
        self.qa('feedback', shot, '--status', 'accepted')
        gate = self.qa('gate', shot, '--project-root', self.root, code=1)
        self.assertIn('user acceptance provenance required', gate['reasons'])
        history = self.qa('history', '--project-root', self.root, '--item-id', 'F-1')
        self.record()
        gate = self.qa('gate', shot, '--project-root', self.root,
                       '--expected-revision', history['revision'], code=1)
        self.assertIn('stale Item revision', gate['reasons'])

    def test_retention_previews_exact_records_and_deletion_invalidates_history(self):
        shot = self.record()
        preview = self.qa('retention', '--project-root', self.root, '--item-id', 'F-1')
        self.assertEqual(preview['paths'], [shot])
        self.assertTrue(Path(shot).exists())
        self.qa('retention', '--project-root', self.root, '--item-id', 'F-1',
                '--delete', '--expected-revision', preview['revision'])
        self.assertFalse(Path(shot).exists())
        tombstone = next((self.root / '.audit/deleted').glob('*.json'))
        self.assertEqual(set(json.loads(tombstone.read_text())), {'shot_id', 'item_id', 'status'})
        self.qa('retention', '--project-root', self.root, '--item-id', 'F-1',
                '--delete', '--expected-revision', preview['revision'], code=4)
        history = self.qa('history', '--project-root', self.root, '--item-id', 'F-1')
        self.assertEqual(history['deleted_shots'], 1)

    def test_sourced_acceptance_still_refuses_veto_and_mismatched_proof(self):
        result = self.qa('record', 'fixture', '--project-root', self.root,
            '--item-id', 'F-1', '--request', self.root / 'request.txt',
            '--output-manifest', self.root / 'manifest.json', '--gates', self.root / 'gates.json',
            '--changed', 'outside.txt', '--within', 'src/')
        shot = result['path']
        self.qa('feedback', shot, '--status', 'accepted', '--source-kind', 'user',
            '--source-ref', 'fixture:turn', '--source-text', 'Accepted',
            '--observed-at', '2026-09-05T00:00:00Z')
        gate = self.qa('gate', shot, '--project-root', self.root,
                       '--proof', 'different-proof.txt', code=1)
        self.assertIn('scope_breach', gate['reasons'])
        self.assertIn('proof coverage missing: different-proof.txt', gate['reasons'])

    def test_concurrent_feedback_preserves_each_operation_and_conflicts_are_explicit(self):
        shot = self.record()
        commands = [[sys.executable, str(QA), 'feedback', shot, '--rank', str(rank),
                     '--operation-id', f'rank-{rank}', '--json'] for rank in range(4)]
        processes = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for cmd in commands]
        for process in processes:
            stdout, stderr = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, stdout + stderr)
        history = self.qa('history', '--project-root', self.root, '--item-id', 'F-1')
        self.assertEqual(history['feedback_events'], 4)
        self.qa('feedback', shot, '--rank', '99', '--operation-id', 'rank-0', code=4)
        self.qa('feedback', shot, '--status', 'accepted', '--expected-revision', 'stale', code=4)

    def test_portable_code_proof_needs_no_aesthetic_or_host_transcript(self):
        (self.root / 'answer.py').write_text('def answer(): return 42\n')
        (self.root / 'code.json').write_text(json.dumps({'adapter': 'code', 'artifacts': [
            {'role': 'deliverable', 'path': 'answer.py'}, {'role': 'proof', 'path': 'check.txt'}]}))
        result = self.run_command(ROOT / 'cook/prove.py', '--project-root', self.root,
            '--item-id', 'F-1', '--invocation', 'code-1', '--request', self.root / 'request.txt',
            '--manifest', self.root / 'code.json', '--proof', 'check.txt', '--check',
            sys.executable, '-c', 'from answer import answer; assert answer() == 42; print("pass")')
        shot = result['path']
        self.assertEqual((self.root / 'check.txt').read_text(), 'pass\n')
        self.qa('feedback', shot, '--status', 'accepted', '--source-kind', 'user',
                '--source-ref', 'synthetic:user-turn', '--redacted-ref', 'synthetic:redacted',
                '--observed-at', '2026-09-05T00:00:00Z')
        self.assertTrue(self.qa('gate', shot, '--project-root', self.root)['ready'])
        history = self.qa('history', '--project-root', self.root, '--item-id', 'F-1')
        self.assertIsNone(history['totals_by_profile']['unknown']['input'])

    def test_redacted_request_and_source_do_not_store_original_words(self):
        private = 'private example phrase'
        (self.root / 'request.txt').write_text(private)
        result = self.qa('record', 'fixture', '--project-root', self.root, '--item-id', 'F-1',
            '--request', self.root / 'request.txt', '--inline', 'result',
            '--request-ref', 'user:source', '--redacted-request')
        self.assertNotIn(private, Path(result['path']).read_text())
        self.qa('feedback', result['path'], '--status', 'accepted', '--source-kind', 'user',
            '--source-ref', 'user:turn', '--redacted-ref', 'redacted:turn',
            '--observed-at', '2026-09-05T00:00:00Z')
        self.assertEqual(Path(result['path']).stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
