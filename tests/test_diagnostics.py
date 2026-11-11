import unittest
from tools.diagnose_gemini_connection import classify_results, transport_stage


class DiagnosticTests(unittest.TestCase):
    def test_transport_stage_distinguishes_upload_from_first_response(self):
        metrics = {'time_namelookup': .01, 'time_connect': .02,
                   'time_appconnect': .05, 'size_upload': 120}
        self.assertEqual(transport_stage(metrics), 'tls_complete_request_uploaded_waiting_for_response')
        self.assertEqual(transport_stage({**metrics, 'time_starttransfer': .2}), 'response_started')
        self.assertEqual(transport_stage({'time_connect': .02}), 'tcp_connected')

    def test_metadata_and_timeouts_do_not_prove_quota_or_billing(self):
        result = classify_results([
            {'operation': 'model_metadata', 'http_status': 200},
            {'operation': 'interactions_function_probe', 'http_status': None},
            {'operation': 'generate_content_function_probe', 'http_status': None},
        ])
        self.assertEqual(result['classification'], 'generation_response_missing')
        self.assertIsNone(result['confirmed_cause'])
        result = classify_results([{'operation': 'model_metadata', 'http_status': 200}])
        self.assertEqual(result['classification'], 'generation_not_tested')

    def test_token_count_is_not_generation_success(self):
        result = classify_results([{'operation': 'model_metadata', 'http_status': 200},
                                   {'operation': 'count_tokens', 'http_status': 200},
                                   {'operation': 'plain_text_generation', 'http_status': None}])
        self.assertEqual(result['classification'], 'generation_response_missing')
        self.assertIsNone(result['confirmed_cause'])

    def test_received_headers_do_not_make_incomplete_curl_response_successful(self):
        result = classify_results([{'operation': 'plain_text_generation_curl', 'http_status': 200,
                                    'response_complete': False, 'curl_exit_code': 28}])
        self.assertEqual(result['classification'], 'generation_response_missing')
        self.assertIsNone(result['confirmed_cause'])

    def test_explicit_status_classifications_require_evidence(self):
        for status, expected in [(429, 'quota_or_rate_limit'), (503, 'provider_unavailable'),
                                 (403, 'access_rejected'), (200, 'generation_http_success'), (400, 'other_http_error')]:
            with self.subTest(status=status):
                result = classify_results([{'operation': 'interactions_function_probe', 'http_status': status}])
                self.assertEqual(result['classification'], expected)
