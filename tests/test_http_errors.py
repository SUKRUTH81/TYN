import io
import json
import unittest
from email.message import Message
from urllib.error import HTTPError
from unittest.mock import patch
from release_agent.core import API, APIError


class HTTPErrorTests(unittest.TestCase):
    def test_native_error_message_is_preserved_and_credentials_are_redacted(self):
        api = API('https://generativelanguage.googleapis.com', headers={'x-goog-api-key': 'private-test-key'})
        headers = Message()
        headers['Retry-After'] = '30'
        payload = {'error': {'code': 'service_unavailable', 'message': 'High demand. Key private-test-key must not leak.'}}
        error = HTTPError('https://generativelanguage.googleapis.com/v1beta/interactions', 503, 'Unavailable', headers,
                          io.BytesIO(json.dumps(payload).encode()))
        with patch.object(api.opener, 'open', side_effect=error) as call:
            with self.assertRaises(APIError) as raised:
                api.call('POST', '/v1beta/interactions', {})
        exc = raised.exception
        self.assertEqual(exc.status, 503)
        self.assertEqual(exc.retry_after, 30)
        self.assertEqual(exc.reason, 'service_unavailable')
        self.assertIn('High demand', str(exc))
        self.assertNotIn('private-test-key', str(exc))
        self.assertIn('[REDACTED]', exc.provider_message)
        self.assertEqual(call.call_count, 1)

    def test_timeout_identifies_stage_and_does_not_retry(self):
        api = API('https://generativelanguage.googleapis.com', timeout=120)
        with patch.object(api.opener, 'open', side_effect=TimeoutError) as call:
            with self.assertRaisesRegex(RuntimeError, '120s during POST /v1beta/interactions'):
                api.call('POST', '/v1beta/interactions', {})
        self.assertEqual(call.call_count, 1)
