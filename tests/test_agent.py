import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from release_agent.core import Jira, adf, aggregate, plain
from release_agent.agent import Investigator, calculate_cost, run
from release_agent.importer import import_dataset, validate_dataset


class FakeAPI:
    base = 'https://example.atlassian.net'

    def __init__(self):
        self.issues = {}
        self.bodies = {}
        self.requests = []

    def call(self, method, path, payload=None):
        self.requests.append((method, path, payload))
        if path == '/rest/api/3/search/jql':
            items = list(self.issues.values())
            if 'rr-manifest' in payload['jql']:
                items = [i for i in items if any(x in i['fields']['labels'] for x in ('rr-manifest', 'rr-requirement'))]
            return {'issues': copy.deepcopy(items), 'isLast': True}
        if path == '/rest/api/3/issue' and method == 'POST':
            key = f'TEST-{len(self.issues) + 1}'
            fields = copy.deepcopy(payload['fields'])
            fields['issuelinks'] = []
            self.issues[key] = {'key': key, 'fields': fields}
            self.bodies[key] = []
            return {'key': key}
        if path == '/rest/api/3/issueLink':
            a, b = payload['inwardIssue']['key'], payload['outwardIssue']['key']
            self.issues[a]['fields']['issuelinks'].append({'outwardIssue': {'key': b}})
            self.issues[b]['fields']['issuelinks'].append({'inwardIssue': {'key': a}})
            return {}
        key = path.split('/')[5].split('?')[0]
        if '/comment' in path:
            if method == 'POST':
                self.bodies[key].append({'id': str(len(self.bodies[key]) + 100), 'body': payload['body']})
                return {}
            return {'comments': copy.deepcopy(self.bodies[key]), 'total': len(self.bodies[key])}
        return copy.deepcopy(self.issues[key])


def dataset():
    return {'dataset_label': 'fixture', 'records': [
        {'source_id': sid, 'kind': kind, 'summary': sid, 'release': 'R2.4', 'recorded_status': 'Done',
         'description': description, 'comments': comments, 'links': links}
        for sid, kind, description, comments, links in [
            ('MANIFEST', 'manifest', 'Target: {"release":"R2.4","commit":"b7a91f2","service":"atlas-assistant","environment":"production","prompt":"p7"}\nAll linked requirements mandatory.', [], ['REQ-01']),
            ('REQ-01', 'requirement', 'Mandatory: yes\nAcceptance criterion: all tests pass.', [], ['REC-01']),
            ('REC-01', 'evidence', 'Verification record.', ['Recorded event 2026-11-08T14:00:00+05:30 | actor QA | role QA Lead\nAll tests pass. release R2.4; commit b7a91f2; service atlas-assistant; environment production.', 'duplicate', 'duplicate'], [])]]}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.data = self.path / 'input.json'
        self.data.write_text(json.dumps(dataset()))
        self.api = FakeAPI()
        self.jira = Jira('TEST', 'fixture', self.api)
        import_dataset(self.jira, self.data, output=self.path / 'map.json')

    def report(self):
        return {'requirements': [{'source_id': 'REQ-01', 'mandatory': True, 'decision': 'PASS',
                'explanation': 'QA verified all cases.', 'outstanding': 'None',
                'evidence': [{'key': 'TEST-3', 'comment_id': '100', 'quote': 'All tests pass.', 'stance': 'supports_pass'}]}]}

    def investigator(self):
        agent = Investigator(self.jira, 'R2.4')
        agent.discover()
        for key in ['TEST-1', 'TEST-2', 'TEST-3']:
            agent.read_issue(key)
        return agent

    def test_import_resume_preserves_duplicates(self):
        before = copy.deepcopy(self.api.bodies)
        import_dataset(self.jira, self.data, output=self.path / 'map.json')
        self.assertEqual(len(self.api.issues), 3)
        self.assertEqual(self.api.bodies, before)
        self.assertEqual(len(before['TEST-3']), 3)
        self.assertIn('Recorded event', plain(before['TEST-3'][0]['body']))

    def test_complete_supplied_dataset_import_and_resume(self):
        path = Path(__file__).resolve().parents[1] / 'inputs' / 'dataset.json'
        api = FakeAPI()
        jira = Jira('TEST', 'tyn-release-assessment-v2', api)
        with contextlib.redirect_stdout(io.StringIO()):
            first = import_dataset(jira, path, output=self.path / 'full-map.json')
            before = copy.deepcopy(api.bodies)
            second = import_dataset(jira, path, output=self.path / 'full-map.json')
        self.assertEqual(first, second)
        self.assertEqual(first['issues'], 400)
        self.assertEqual(first['comments'], 2059)
        self.assertEqual(api.bodies, before)
        investigator = Investigator(jira, 'R2.4')
        investigator.discover()
        # Fake search lacks release filtering; this input has exactly twelve requirement records.
        self.assertEqual(len(investigator.requirements), 12)

    def test_adf_roundtrip(self):
        text = 'first\n\nsecond — Unicode'
        self.assertEqual(plain(adf(text)).rstrip(), text)

    def test_input_rejects_dangling(self):
        data = dataset()
        data['records'][0]['links'] = ['missing']
        with self.assertRaises(ValueError):
            validate_dataset(data)

    def test_aggregation(self):
        for decisions, expected in [(['PASS'], 'READY'), (['PASS', 'FAIL'], 'BLOCKED'),
                                    (['INSUFFICIENT_EVIDENCE'], 'NEEDS_REVIEW'),
                                    (['FAIL', 'INSUFFICIENT_EVIDENCE'], 'BLOCKED')]:
            self.assertEqual(aggregate([{'mandatory': True, 'decision': d} for d in decisions]), expected)

    def test_scope_gate(self):
        self.api.issues['TEST-3']['fields']['labels'] = ['other']
        with self.assertRaises(ValueError):
            self.jira.issue('TEST-3')

    def test_undiscovered_issue(self):
        with self.assertRaises(ValueError):
            Investigator(self.jira, 'R2.4').read_issue('TEST-3')

    def test_valid_report(self):
        report = self.investigator().submit_report(json.dumps(self.report()))
        self.assertEqual(report['overall_decision'], 'READY')
        self.assertIn('focusedCommentId=100', report['requirements'][0]['evidence'][0]['url'])

    def test_fabricated_quote_rejected(self):
        report = self.report()
        report['requirements'][0]['evidence'][0]['quote'] = 'fabricated'
        with self.assertRaises(ValueError):
            self.investigator().submit_report(json.dumps(report))

    def test_mandatory_downgrade_rejected(self):
        report = self.report()
        report['requirements'][0]['mandatory'] = False
        with self.assertRaises(ValueError):
            self.investigator().submit_report(json.dumps(report))

    def test_unread_dependency_rejected(self):
        agent = self.investigator()
        del agent.read['TEST-3']
        with self.assertRaises(ValueError):
            agent.submit_report(json.dumps(self.report()))

    def test_missing_requirement_rejected(self):
        with self.assertRaises(ValueError):
            self.investigator().submit_report('{"requirements": []}')

    def test_cost(self):
        result = calculate_cost(input_tokens=1000000, cached_tokens=500000, output_tokens=100000,
                                input_rate=2, cached_rate=1, output_rate=10, successful_requests=1000)
        self.assertEqual(result['mean_usd_per_success'], '0.0025')
        with self.assertRaises(ValueError):
            calculate_cost(input_tokens=1, cached_tokens=2, output_tokens=0, input_rate=1,
                           cached_rate=1, output_rate=1, successful_requests=1)

    def test_comment_pagination_and_truncation_error(self):
        class Pages:
            def __init__(self, empty=False):
                self.calls = 0
                self.empty = empty
            def call(self, method, path):
                self.calls += 1
                return {'total': 2, 'comments': [] if self.empty else [{'id': str(self.calls)}]}
        api = Pages()
        jira = Jira('TEST', 'fixture', api)
        self.assertEqual([c['id'] for c in jira.comments('TEST-1')], ['1', '2'])
        with self.assertRaises(RuntimeError):
            Jira('TEST', 'fixture', Pages(True)).comments('TEST-1')

    def test_search_pagination_preserves_scope(self):
        class Pages:
            def __init__(self):
                self.calls = []
            def call(self, method, path, payload):
                self.calls.append(payload)
                if len(self.calls) == 1:
                    return {'issues': [{'key': 'TEST-1'}], 'nextPageToken': 'page-two'}
                return {'issues': [{'key': 'TEST-2'}], 'isLast': True}
        api = Pages()
        result = Jira('TEST', 'fixture', api).search()
        self.assertEqual(len(result), 2)
        self.assertEqual(api.calls[1]['nextPageToken'], 'page-two')
        for call in api.calls:
            self.assertIn('project = "TEST" AND labels = "fixture"', call['jql'])

    def test_model_failure_records_no_success_report(self):
        class BrokenModel:
            def call(self, *args):
                raise RuntimeError('Model unavailable')
        output = self.path / 'model-failure'
        with self.assertRaisesRegex(RuntimeError, 'Model unavailable'):
            run(self.jira, 'R2.4', output, 'scripted-test-double', model_api=BrokenModel())
        self.assertEqual(json.loads((output / 'metrics.json').read_text())['status'], 'FAILED')
        self.assertFalse((output / 'report.md').exists())

    def test_scripted_protocol_end_to_end_and_failure_artifacts(self):
        report = self.report()
        class Model:
            def __init__(self):
                self.actions = iter([('discover', {}), ('read_issue', {'key': 'TEST-1'}),
                    ('declare_requirements', {'source_ids': ['REQ-01']}), ('read_issue', {'key': 'TEST-2'}),
                    ('get_linked_issues', {'key': 'TEST-2', 'depth': 3, 'limit': 40}),
                    ('verify_evidence_scope', {'key': 'TEST-3', 'comment_id': '100'}),
                    ('submit_decision', {'report_json': json.dumps(report)})])
            def call(self, *args):
                name, arguments = next(self.actions)
                return {'id': 'mock', 'status': 'completed', 'usage': {'total_tokens': 10}, 'output': [
                    {'type': 'function_call', 'name': name, 'call_id': name, 'arguments': json.dumps(arguments)}]}
        output = self.path / 'success'
        result = run(self.jira, 'R2.4', output, 'scripted-test-double', model_api=Model())
        self.assertEqual(result['overall_decision'], 'READY')
        self.assertEqual(json.loads((output / 'metrics.json').read_text())['tool_calls'], 7)
        failed = self.path / 'failed'
        with self.assertRaises(RuntimeError):
            run(self.jira, 'R2.4', failed, 'scripted-test-double', max_calls=1, model_api=Model())
        self.assertEqual(json.loads((failed / 'metrics.json').read_text())['status'], 'FAILED')
        self.assertFalse((failed / 'report.json').exists())


if __name__ == '__main__':
    unittest.main()
