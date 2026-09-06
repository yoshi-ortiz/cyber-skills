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

    def test_feedback_proof_and_next_feature(self):
        self.assertEqual(self.next()['item_id'], 'F-1')
        shot = self.record()
        self.assertEqual(self.next()['next_action'], 'await-feedback')
        rejected = self.qa('feedback', shot, '--status', 'rejected', '--correction', 'Fix the result')
        result = self.next()
        self.assertEqual(result['next_action'], 'apply-correction')
        self.assertEqual(result['observations']['latest']['correction'], 'Fix the result')
        shot = self.record()
        self.qa('feedback', shot, '--status', 'accepted', '--resolve', rejected['event_id'],
                '--source-kind', 'user', '--source-ref', 'synthetic:user-turn',
                '--source-text', 'Accepted', '--observed-at', '2026-09-05T00:00:00Z')
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

    def test_reviewed_contract_produces_complete_deterministic_decision(self):
        (self.root / 'ROADMAP.md').write_text(
            '| ID | State | Item | Workstream | Contract |\n'
            '| --- | --- | --- | --- | --- |\n'
            '| F-1 | IN-PROGRESS | Deliver proof | default | item.json |\n')
        contract = {'version': 1, 'item_id': 'F-1', 'review_ref': 'user:approval',
                    'acceptance_criteria': ['Proof is readable'], 'exclusions': [],
                    'read_paths': ['request.txt'], 'write_paths': ['proof.txt'],
                    'proof_requirements': ['proof.txt'], 'budget_tokens': 1000}
        (self.root / 'item.json').write_text(json.dumps(contract))
        decision = self.next()
        self.assertEqual(decision['next_action'], 'continue-task')
        self.assertEqual(decision['version'], 1)
        self.assertEqual(decision['acceptance_criteria'], ['Proof is readable'])
        self.assertEqual(decision['write_paths'], ['proof.txt'])
        self.assertEqual(decision['budget']['status'], 'available')
        self.assertEqual(decision, self.next())
        contract['write_paths'] = []
        contract['budget_tokens'] = 0
        (self.root / 'item.json').write_text(json.dumps(contract))
        self.assertEqual(self.next()['next_action'], 'budget-exhausted')
        del contract['acceptance_criteria']
        (self.root / 'item.json').write_text(json.dumps(contract))
        decision = self.next()
        self.assertEqual(decision['next_action'], 'bound-task')
        self.assertIn('acceptance_criteria required', decision['reasons'])
        contract['acceptance_criteria'] = False
        (self.root / 'item.json').write_text(json.dumps(contract))
        invalid = subprocess.run([sys.executable, str(CONTEXT), '--root', str(self.root),
                                  '--json', 'next'], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn('acceptance_criteria', invalid.stderr)
        self.assertNotIn('Traceback', invalid.stderr)

    def test_pending_and_proof_decisions_explain_their_blockers(self):
        shot = self.record()
        pending = self.next()
        self.assertEqual(pending['latest_shot']['path'], shot)
        self.assertEqual(pending['effective_feedback']['status'], 'pending')
        self.assertIn('await-feedback', pending['reasons'])
        self.assertIn('acceptance_criteria', pending)
        self.qa('feedback', shot, '--status', 'accepted')
        (self.root / 'proof.txt').write_text('changed proof')
        decision = self.next()
        self.assertEqual(decision['next_action'], 'verify-proof')
        self.assertIn('artifact[0]: hash mismatch or absent', decision['reasons'])
        self.assertIn('budget', decision)

    def test_missing_contract_file_returns_bounded_requirement(self):
        (self.root / 'ROADMAP.md').write_text(
            '| ID | State | Workstream | Contract |\n'
            '| --- | --- | --- | --- |\n'
            '| F-1 | TODO | default | missing.json |\n')
        decision = self.next()
        self.assertEqual(decision['next_action'], 'bound-task')
        self.assertEqual(decision['reasons'], ['contract required: missing.json'])

    def test_explicit_selection_matches_standalone_and_never_falls_back(self):
        selector = ROOT / 'first/genesis/scripts/compass.py'
        (self.root / 'ROADMAP.md').write_text(
            '| ID | State | Workstream | Scope | Proof | Priority | Deferred | Depends on |\n'
            '| --- | --- | --- | --- | --- | --- | --- | --- |\n'
            '| F-1 | IN-PROGRESS | default | src/ | test | 9 | false | |\n'
            '| F-2 | TODO | default | src/ | test | 0 | false | |\n'
            '| F-3 | TODO | default | src/ | test | 0 | true | |\n'
            '| F-4 | BLOCKED | default | src/ | test | 0 | false | |\n'
            '| F-5 | TODO | default | src/ | test | 0 | false | F-1 |\n')
        for args in ([], ['--item', 'F-2']):
            standalone = self.run_command(selector, '--project-root', self.root, 'next', *args)
            joined = self.run_command(CONTEXT, '--root', self.root, '--json', 'next', *args)
            self.assertEqual(joined['item_id'], standalone['item_id'])
        for identity in ('F-3', 'F-4', 'F-5', 'missing'):
            result = subprocess.run([sys.executable, str(CONTEXT), '--root', str(self.root),
                                     '--json', 'next', '--item', identity], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('Traceback', result.stderr)

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
