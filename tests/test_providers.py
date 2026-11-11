import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from release_agent.agent import TOOLS, run
from release_agent.providers import DEFAULT_MODEL, GeminiAPI, default_model, model_key_name
from release_agent.core import Jira
from release_agent.core import APIError
from release_agent.importer import import_dataset
from tests.test_agent import FakeAPI, dataset


def reply(name='discover', arguments=None, call_id='call-1', status='requires_action'):
    return {'id': 'interaction-1', 'model': DEFAULT_MODEL, 'status': status, 'steps': [
        {'type': 'thought', 'signature': 'opaque-signature'},
        {'type': 'function_call', 'id': call_id, 'name': name, 'arguments': arguments or {}}],
        'usage': {'total_input_tokens': 20, 'total_output_tokens': 5, 'total_thought_tokens': 3,
                  'total_cached_tokens': 10, 'total_tokens': 28}}


class Transport:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def call(self, method, path, payload):
        self.requests.append((method, path, copy.deepcopy(payload)))
        return next(self.responses)


class GeminiTests(unittest.TestCase):
    def payload(self, history=None):
        return {'model': DEFAULT_MODEL, 'instructions': 'Use Jira only', 'tools': TOOLS,
                'max_output_tokens': 10000, 'input': history or [{'role': 'user', 'content': 'Assess target'}]}

    def test_native_gemini_request_and_usage(self):
        transport = Transport([reply()])
        result = GeminiAPI(transport).call('POST', '/v1/responses', self.payload())
        method, path, payload = transport.requests[0]
        self.assertEqual((method, path), ('POST', '/v1beta/interactions'))
        self.assertEqual(payload['model'], 'gemini-3.8-flash')
        self.assertFalse(payload['store'])
        self.assertEqual(payload['system_instruction'], 'Use Jira only')
        self.assertEqual(payload['generation_config']['thinking_level'], 'medium')
        self.assertEqual(payload['generation_config']['tool_choice']['allowed_tools']['mode'], 'any')
        self.assertNotIn('strict', payload['tools'][0])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['usage']['total_tokens'], 28)
        self.assertEqual(result['usage']['reasoning_tokens'], 3)
        self.assertEqual(result['usage']['cached_input_tokens'], 10)

    def test_full_steps_and_call_ids_survive_tool_round_trip(self):
        raw = reply()
        transport = Transport([raw, reply(name='read_issue', call_id='call-2')])
        api = GeminiAPI(transport)
        payload = self.payload()
        first = api.call('POST', '/v1/responses', payload)
        history = payload['input'] + first['output'] + [
            {'type': 'function_call_output', 'call_id': 'call-1', 'output': '[{"key":"TEST-1"}]'}]
        api.call('POST', '/v1/responses', self.payload(history))
        second = transport.requests[1][2]
        self.assertEqual(second['input'][1:3], raw['steps'])
        self.assertEqual(second['input'][-1], {'type': 'function_result', 'name': 'discover', 'call_id': 'call-1',
                         'result': [{'type': 'text', 'text': '[{"key":"TEST-1"}]'}]})
        self.assertEqual(second['system_instruction'], 'Use Jira only')

    def test_failures_are_not_mapped_to_success(self):
        raw = reply(status='incomplete')
        result = GeminiAPI(Transport([raw])).call('POST', '/v1/responses', self.payload())
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual(result['provider_response'], raw)
        raw = reply()
        del raw['steps'][1]['id']
        with self.assertRaisesRegex(RuntimeError, 'valid ID'):
            GeminiAPI(Transport([raw])).call('POST', '/v1/responses', self.payload())

    def test_default_and_required_key_are_provider_specific(self):
        with patch.dict(os.environ, {'GEMINI_MODEL': '', 'MODEL_PROVIDER': 'gemini'}):
            self.assertEqual(default_model(), 'gemini-3.8-flash')
        self.assertEqual(model_key_name('gemini-3.8-flash'), 'GEMINI_API_KEY')
        self.assertEqual(model_key_name('gpt-5.4'), 'OPENAI_API_KEY')
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            with self.assertRaisesRegex(ValueError, 'GEMINI_API_KEY'):
                GeminiAPI()

    def test_only_explicit_rate_limit_rejections_are_retried(self):
        class Limited:
            def __init__(self, status):
                self.calls, self.status = 0, status
            def call(self, *args):
                self.calls += 1
                if self.calls == 1:
                    raise APIError('rate limit', self.status, 2)
                return reply()
        transport = Limited(429)
        with patch('release_agent.providers.time.sleep') as sleep:
            result = GeminiAPI(transport).call('POST', '/v1/responses', self.payload())
        self.assertEqual(result['rate_limit_retries'], 1)
        sleep.assert_called_once_with(2)
        transport = Limited(503)
        with self.assertRaises(APIError):
            GeminiAPI(transport).call('POST', '/v1/responses', self.payload())
        self.assertEqual(transport.calls, 1)

    def test_key_uses_google_header_not_url_or_openai_authorization(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'secret-google-key'}), patch('release_agent.providers.API') as http:
            GeminiAPI()
            http.assert_called_once_with('https://generativelanguage.googleapis.com', headers={'x-goog-api-key': 'secret-google-key'}, timeout=120.0)

    def test_native_gemini_investigation_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_file = root / 'input.json'
            input_file.write_text(json.dumps(dataset()))
            jira = Jira('TEST', 'fixture', FakeAPI())
            import_dataset(jira, input_file, output=root / 'map.json')
            report = {'requirements': [{'source_id': 'REQ-01', 'mandatory': True, 'decision': 'PASS',
                'explanation': 'QA verified all tests.', 'outstanding': 'None',
                'evidence': [{'key': 'TEST-3', 'comment_id': '100', 'quote': 'All tests pass.', 'stance': 'supports_pass'}]}]}
            actions = [('discover', {}), ('read_issue', {'key': 'TEST-1'}),
                       ('declare_requirements', {'source_ids': ['REQ-01']}), ('read_issue', {'key': 'TEST-2'}),
                       ('get_linked_issues', {'key': 'TEST-2', 'depth': 3, 'limit': 40}),
                       ('verify_evidence_scope', {'key': 'TEST-3', 'comment_id': '100'}),
                       ('submit_decision', {'report_json': json.dumps(report)})]
            transport = Transport([reply(name, args, f'call-{index}') for index, (name, args) in enumerate(actions)])
            output = root / 'run'
            result = run(jira, 'R2.4', output, DEFAULT_MODEL, model_api=GeminiAPI(transport))
            self.assertEqual(result['overall_decision'], 'READY')
            metrics = json.loads((output / 'metrics.json').read_text())
            self.assertEqual(metrics['provider'], 'gemini')
            self.assertEqual(metrics['usage']['total_tokens'], 196)
            self.assertEqual(metrics['usage']['reasoning_tokens'], 21)
            self.assertEqual(metrics['model_calls'], 7)
            self.assertEqual(transport.requests[-1][2]['input'][-1]['name'], 'verify_evidence_scope')
            self.assertTrue((output / 'trace.jsonl').exists())

    def test_missing_gemini_key_writes_failure_metrics(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            output = Path(temp)
            with self.assertRaisesRegex(RuntimeError, 'GEMINI_API_KEY'):
                run(Jira('TEST', 'fixture', FakeAPI()), 'R2.4', output, DEFAULT_MODEL)
            self.assertEqual(json.loads((output / 'metrics.json').read_text())['status'], 'FAILED')
