import json
import tempfile
import unittest
from pathlib import Path
from release_agent.visual_report import write_visual_report


class VisualReportTests(unittest.TestCase):
    def test_untrusted_evidence_is_escaped_and_execution_failure_is_not_a_verdict(self):
        report = {'assessment_complete': False, 'release': 'R2.4', 'overall_decision': 'NEEDS_REVIEW',
                  'requirements': [{'source_id': 'REQ-01', 'decision': 'INSUFFICIENT_EVIDENCE',
                      'assessment_status': 'ERROR', 'explanation': '<script>alert(1)</script>',
                      'evidence': [{'key': 'TYN-1', 'url': 'javascript:alert(1)', 'quote': '<img src=x onerror=alert(1)>'}]}]}
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, 'report.json').write_text(json.dumps(report), encoding='utf-8')
            output = write_visual_report(temp).read_text(encoding='utf-8')
        self.assertIn('INCOMPLETE ASSESSMENT', output)
        self.assertIn('NOT ASSESSED', output)
        self.assertIn('&lt;script&gt;', output)
        self.assertNotIn('<script>', output)
        self.assertNotIn('href="javascript:', output)
        self.assertNotIn('<img', output)

    def test_complete_report_keeps_jira_comment_links_and_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            report = {'assessment_complete': True, 'requirements': [
                {'source_id': 'REQ-01', 'decision': 'PASS', 'assessment_status': 'COMPLETE',
                 'evidence': [{'key': 'TYN-1', 'comment_id': '123', 'quote': 'All cases pass.',
                     'url': 'https://example.atlassian.net/browse/TYN-1?focusedCommentId=123'}]}]}
            Path(temp, 'report.json').write_text(json.dumps(report), encoding='utf-8')
            Path(temp, 'metrics.json').write_text(json.dumps({'elapsed_seconds': 10, 'usage_complete': True,
                                                           'usage': {'total_tokens': 1234}}), encoding='utf-8')
            output = write_visual_report(temp).read_text(encoding='utf-8')
        self.assertIn('focusedCommentId=123', output)
        self.assertIn('1,234 reported tokens', output)
        self.assertNotIn('INCOMPLETE ASSESSMENT', output)
