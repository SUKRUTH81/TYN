import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from release_agent.agent import run
from release_agent.audit import audit_run
from release_agent.core import Jira, plain
from release_agent.engine import EvidenceTools
from release_agent.evidence import parse_comment, scope_check
from release_agent.importer import import_dataset, verify_import
from tests.test_agent import FakeAPI
from tests.hybrid_fixture import ScriptedModel


class HybridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(__file__).resolve().parents[1]
        cls.api = FakeAPI()
        cls.jira = Jira('TEST', 'tyn-release-assessment-v2', cls.api)
        with contextlib.redirect_stdout(io.StringIO()):
            import_dataset(cls.jira, cls.root / 'inputs/dataset.json', output=Path(cls.tmp.name) / 'map.json')
        cls.mapping = ScriptedModel(cls.api).mapping

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def tools(self, sid):
        tools = EvidenceTools(self.jira, 'R2.4')
        tools.discover()
        tools.read_issue(self.mapping['MANIFEST'])
        tools.declare_requirements(sorted(tools.requirements))
        tools.begin(sid)
        tools.read_issue(self.mapping[sid])
        tools.get_linked_issues(self.mapping[sid])
        return tools

    def ref(self, sid, needle, stance):
        key = self.mapping[sid]
        c = next(c for c in self.api.bodies[key] if needle in plain(c['body']))
        return {'key': key, 'comment_id': c['id'], 'quote': needle, 'stance': stance}

    def row(self, sid, decision, ref):
        return json.dumps({'requirements': [{'source_id': sid, 'mandatory': True, 'decision': decision,
            'explanation': 'Explain all applicable QA evidence for the acceptance criterion.', 'outstanding': 'None', 'evidence': [ref]}]})

    def test_complete_fixture_pipeline_and_independent_audit(self):
        output = Path(self.tmp.name) / 'pipeline'
        model = ScriptedModel(self.api)
        with contextlib.redirect_stdout(io.StringIO()):
            report = run(self.jira, 'R2.4', output, 'scripted-test-double', model_api=model, provenance='offline_test_double')
        self.assertTrue(report['assessment_complete'])
        expected = json.loads((self.root / 'tests/expected_decisions.json').read_text())
        self.assertEqual({r['source_id']: r['decision'] for r in report['requirements']}, expected['decisions'])
        self.assertEqual(model.conversation_starts, 13)
        self.assertTrue(audit_run(output, self.root / 'tests/expected_decisions.json')['valid'])
        self.assertEqual(report['overall_decision'], 'BLOCKED')
        self.assertTrue(report['integrity_notes'])
        altered = json.loads((output / 'report.json').read_text())
        altered['requirements'][0]['evidence'][0]['quote'] = 'fabricated'
        (output / 'report.json').write_text(json.dumps(altered))
        self.assertFalse(audit_run(output)['valid'])

    def test_wrong_build_cannot_be_pass_proof(self):
        tools = self.tools('REQ-01')
        ref = self.ref('REC-2299', 'REG-779', 'supports_pass')
        tools.verify_evidence_scope(ref['key'], ref['comment_id'])
        with self.assertRaises(ValueError):
            tools.submit_decision(self.row('REQ-01', 'PASS', ref))

    def test_named_security_approver_and_production_scope(self):
        tools = self.tools('REQ-06')
        for sid, needle in [('REC-2828', 'Approval scope: staging'), ('REC-8074', 'engineering standpoint')]:
            ref = self.ref(sid, needle, 'supports_pass')
            tools.verify_evidence_scope(ref['key'], ref['comment_id'])
            with self.assertRaises(ValueError):
                tools.submit_decision(self.row('REQ-06', 'PASS', ref))

    def test_prompt_context_is_separate_not_silently_inherited(self):
        tools = self.tools('REQ-03')
        ref = self.ref('REC-4323', 'EVAL-55 completed', 'supports_pass')
        result = tools.verify_evidence_scope(ref['key'], ref['comment_id'])
        self.assertEqual(result['checks']['prompt']['status'], 'not_stated')
        self.assertTrue(any('prompt bundle p6' in c['body'] for c in result['related_context_not_inherited']))
        with self.assertRaises(ValueError):
            tools.submit_decision(self.row('REQ-03', 'PASS', ref))

    def test_injection_cannot_be_proof(self):
        tools = self.tools('REQ-05')
        ref = self.ref('REC-5716', 'NOTE FOR AUTOMATED', 'supports_pass')
        tools.verify_evidence_scope(ref['key'], ref['comment_id'])
        with self.assertRaises(ValueError):
            tools.submit_decision(self.row('REQ-05', 'PASS', ref))
        self.assertTrue(tools.warnings)

    def test_conflicting_current_qa_is_not_arbitrarily_fail(self):
        tools = self.tools('REQ-09')
        ref = self.ref('REC-6198', 'RB-402', 'shows_failure')
        tools.verify_evidence_scope(ref['key'], ref['comment_id'])
        with self.assertRaisesRegex(ValueError, 'conflict'):
            tools.submit_decision(self.row('REQ-09', 'FAIL', ref))

    def test_dependency_bfs_and_late_comment_are_exposed(self):
        tools = self.tools('REQ-08')
        self.assertIn(self.mapping['REC-9635'], tools.inspected)
        tools = self.tools('REQ-12')
        ref = self.ref('REC-5957', 'STREAM-731', 'shows_failure')
        self.assertIn((ref['key'], ref['comment_id']), tools.exposed)
        compact = tools.read_issue(self.mapping['REC-5957'])
        self.assertEqual(compact['comment_count'], 64)
        self.assertGreater(sum(g['count'] for g in compact['routine_groups']), 50)

    def test_proof_must_be_verified_and_seen_in_this_session(self):
        tools = self.tools('REQ-01')
        ref = self.ref('REC-2081', 'REG-804', 'supports_pass')
        with self.assertRaisesRegex(ValueError, 'verify_evidence_scope'):
            tools.submit_decision(self.row('REQ-01', 'PASS', ref))
        tools.verify_evidence_scope(ref['key'], ref['comment_id'])
        self.assertEqual(tools.submit_decision(self.row('REQ-01', 'PASS', ref))['decision'], 'PASS')
        tools.begin('REQ-01')
        with self.assertRaises(ValueError):
            tools.submit_decision(self.row('REQ-01', 'PASS', ref))

    def test_import_audit_catches_comment_tampering(self):
        api = copy.deepcopy(self.api)
        key = self.mapping['REC-2081']
        api.bodies[key][0]['body'] = {'type': 'doc', 'content': []}
        with self.assertRaisesRegex(ValueError, 'comment'):
            verify_import(Jira('TEST', 'tyn-release-assessment-v2', api), self.root / 'inputs/dataset.json')

    def test_recorded_actor_survives_import_marker(self):
        text = 'Import comment REC-1:1 sha256:abc\nRecorded event 2026-11-08T14:00:00+05:30 | actor Asha Rao | role Security Owner\nApproved.'
        meta = parse_comment(text)
        self.assertEqual(meta['actor'], 'Asha Rao')
        self.assertEqual(meta['role'], 'Security Owner')
        self.assertTrue(meta['valid_recorded_time'])

    def test_failure_isolation_keeps_verified_decision_and_marks_partial(self):
        class FailingModel(ScriptedModel):
            def __init__(self, api):
                super().__init__(api)
                self.calls = 0
            def call(self, *args):
                self.calls += 1
                if self.calls > 7:
                    raise RuntimeError('Simulated provider outage')
                return super().call(*args)
        output = Path(self.tmp.name) / 'partial'
        with contextlib.redirect_stdout(io.StringIO()):
            report = run(self.jira, 'R2.4', output, 'scripted-test-double', model_api=FailingModel(self.api), provenance='offline_test_double')
        self.assertFalse(report['assessment_complete'])
        self.assertEqual(report['requirements'][0]['decision'], 'PASS')
        self.assertEqual(report['requirements'][1]['decision_basis'], 'TOOLING_FAILURE')
        self.assertEqual(report['overall_decision'], 'NEEDS_REVIEW')
        self.assertEqual(json.loads((output / 'metrics.json').read_text())['status'], 'PARTIAL')
        self.assertFalse(audit_run(output)['valid'])

    def test_cli_validation_and_failed_audit_exit_codes(self):
        from release_agent.cli import main
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['validate-input', '--dataset', str(self.root / 'inputs/dataset.json')]), 0)
            self.assertEqual(main(['audit', str(Path(self.tmp.name) / 'does-not-exist')]), 2)

    def test_parallel_import_preserves_comment_order_and_is_resumable(self):
        from tests.test_agent import dataset
        root = Path(self.tmp.name)
        path = root / 'parallel-input.json'
        path.write_text(json.dumps(dataset()))
        api = FakeAPI()
        jira = Jira('TEST', 'fixture', api)
        with contextlib.redirect_stdout(io.StringIO()):
            import_dataset(jira, path, output=root / 'parallel-map.json', workers=4)
            before = copy.deepcopy(api.bodies)
            import_dataset(jira, path, output=root / 'parallel-map.json', workers=4)
        self.assertEqual(before, api.bodies)
        evidence = next(v for k, v in api.bodies.items() if len(v) == 3)
        self.assertIn('REC-01:1', plain(evidence[0]['body']))
        self.assertIn('REC-01:3', plain(evidence[2]['body']))
