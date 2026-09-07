"""Public Compass selection and decision regressions."""
import json
import subprocess
import sys
import unittest

from compass_flow_case import CompassFlowCase, CONTEXT, QA, ROOT


class CompassFlow(CompassFlowCase):
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

if __name__ == '__main__':
    unittest.main()
