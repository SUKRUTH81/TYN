import os
import unittest
from unittest.mock import patch
from release_agent.providers import GroqAPI, default_model, model_key_name, model_provider
from release_agent.core import APIError
from tests.test_providers import Transport


class GroqTests(unittest.TestCase):
    def test_rejected_tool_generation_gets_one_correction_without_expanding_tools(self):
        from unittest.mock import Mock
        rejected = APIError('Tool call validation failed', 400, reason='tool_use_failed')
        raw = {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
            {'id': 'c1', 'function': {'name': 'read_issue', 'arguments': '{"key":"TYN-1"}'}}]}}]}
        requests = []
        def send(method, path, payload):
            import copy
            requests.append(copy.deepcopy(payload))
            if len(requests) == 1:
                raise rejected
            return raw
        transport = Transport([])
        transport.call = Mock(side_effect=send)
        result = GroqAPI(transport).call('POST', '/v1/responses', self.payload())
        self.assertEqual(result['tool_validation_recoveries'], 1)
        self.assertEqual(requests[0]['tools'], requests[1]['tools'])
        self.assertNotIn('disable_tool_validation', requests[1])
        self.assertIn('Choose only a tool from this turn: read_issue', requests[1]['messages'][0]['content'])
        self.assertEqual(result['output'][0]['name'], 'read_issue')

    def test_repeated_tool_validation_error_stops_after_one_correction(self):
        from unittest.mock import Mock
        transport = Transport([])
        transport.call = Mock(side_effect=APIError('invalid tools', 400, reason='tool_use_failed'))
        with self.assertRaises(APIError):
            GroqAPI(transport).call('POST', '/v1/responses', self.payload())
        self.assertEqual(transport.call.call_count, 2)

    def test_only_short_explicit_rate_limit_rejections_are_retried(self):
        for status, delay, retry in [(429, 3, True), (429, 90, False), (429, None, False), (503, 3, False)]:
            transport = Transport([])
            from unittest.mock import Mock
            transport.call = Mock(side_effect=[APIError('rejected', status, delay), {'ok': True}])
            with patch('release_agent.providers.time.sleep') as sleep:
                if retry:
                    raw, retries = GroqAPI(transport).send({})
                    self.assertEqual((raw, retries), ({'ok': True}, 1))
                    sleep.assert_called_once_with(3)
                else:
                    with self.assertRaises(APIError):
                        GroqAPI(transport).send({})
                    sleep.assert_not_called()

    def payload(self, history=None):
        return {'model': 'groq/openai/gpt-oss-120b', 'instructions': 'Read Jira only',
                'input': history or [{'role': 'user', 'content': 'Assess'}],
                'tools': [{'name': 'read_issue', 'description': 'Read', 'parameters': {'type': 'object'}}],
                'max_output_tokens': 1024}

    def test_tool_roundtrip_usage_and_routing(self):
        raw = {'id': 'r1', 'model': 'openai/gpt-oss-120b', 'choices': [{
            'finish_reason': 'tool_calls', 'message': {'tool_calls': [{
                'id': 'c1', 'function': {'name': 'read_issue', 'arguments': '{"key":"TYN-1"}'}}]}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}}
        transport = Transport([raw, raw])
        api = GroqAPI(transport)
        result = api.call('POST', '/v1/responses', self.payload())
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['usage']['total_tokens'], 15)
        self.assertEqual(transport.requests[0][1], '/openai/v1/chat/completions')
        request = transport.requests[0][2]
        self.assertEqual(request['model'], 'openai/gpt-oss-120b')
        self.assertEqual(request['tool_choice'], 'required')
        self.assertFalse(request['parallel_tool_calls'])
        history = self.payload()['input'] + result['output'] + [
            {'type': 'function_call_output', 'call_id': 'c1', 'output': '{"key":"TYN-1"}'}]
        api.call('POST', '/v1/responses', self.payload(history))
        messages = transport.requests[1][2]['messages']
        self.assertEqual(messages[-2]['tool_calls'][0]['id'], 'c1')
        self.assertEqual(messages[-1]['tool_call_id'], 'c1')

    def test_truncated_tool_call_is_not_success(self):
        raw = {'choices': [{'finish_reason': 'length', 'message': {'tool_calls': []}}]}
        result = GroqAPI(Transport([raw])).call('POST', '/v1/responses', self.payload())
        self.assertEqual(result['status'], 'incomplete')

    def test_provider_specific_configuration(self):
        with patch.dict(os.environ, {'MODEL_PROVIDER': 'groq', 'GROQ_MODEL': ''}):
            self.assertEqual(default_model(), 'groq/openai/gpt-oss-120b')
        self.assertEqual(model_key_name('groq/openai/gpt-oss-120b'), 'GROQ_API_KEY')
        self.assertEqual(model_provider('groq/openai/gpt-oss-120b'), 'groq')
        with patch.dict(os.environ, {'GROQ_API_KEY': ''}):
            with self.assertRaisesRegex(ValueError, 'GROQ_API_KEY'):
                GroqAPI()
