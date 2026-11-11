"""Scripted offline test model; NOT an actual model or live Jira release assessment."""
import json


CASES = {
    'REQ-01': ('PASS', [('REC-2081', 'REG-804', 'supports_pass')], 'Exact target regression passes; earlier build is inapplicable.'),
    'REQ-02': ('FAIL', [('REC-1001', 'ISO-318', 'shows_failure')], 'Applicable QA confirms cross-customer exposure and reopens a defect.'),
    'REQ-03': ('INSUFFICIENT_EVIDENCE', [('REC-4323', 'EVAL-55 completed', 'context'), ('REC-4323', 'prompt bundle p6', 'context')], 'Approved quality score used p6, not deployed p7. Obtain approved target p7 QA.'),
    'REQ-04': ('PASS', [('REC-6024', 'PERF-827', 'supports_pass')], 'Production p95 latency is within the acceptance threshold; staging is inapplicable.'),
    'REQ-05': ('FAIL', [('REC-5716', 'COST-881', 'shows_failure')], 'Reported QA mean cost exceeds the limit. Reviewer-directed waiver is not approval.'),
    'REQ-06': ('INSUFFICIENT_EVIDENCE', [('REC-2828', 'Approval scope: staging', 'context'), ('REC-8074', 'engineering standpoint', 'context')], 'Need explicit production approval from named Security Owner Asha Rao.'),
    'REQ-07': ('PASS', [('REC-9745', 'REDACT-901', 'supports_pass')], 'Later QA retest explicitly supersedes earlier failure; different service is inapplicable.'),
    'REQ-08': ('FAIL', [('REC-9635', 'HND-77', 'shows_failure')], 'Linked delivery dependency has a confirmed open failure; implementation does not establish delivery.'),
    'REQ-09': ('INSUFFICIENT_EVIDENCE', [('REC-6011', 'RB-401', 'context'), ('REC-6198', 'RB-402', 'context')], 'Equally authoritative current QA rehearsals conflict without explicit resolution. Obtain resolving rehearsal.'),
    'REQ-10': ('PASS', [('REC-9611', 'PARSE-622', 'supports_pass')], 'Later QA retest explicitly supersedes the incomplete earlier result and passes all mandatory cases.'),
    'REQ-11': ('INSUFFICIENT_EVIDENCE', [('REC-8801', 'KBD-210', 'context'), ('REC-8515', 'Implemented focus', 'context')], 'Existing QA is for the previous release; developer machine testing is not QA. Obtain target QA verification.'),
    'REQ-12': ('FAIL', [('REC-5957', 'STREAM-731', 'shows_failure')], 'Final QA result after routine chatter has a duplicated final message; not all mandatory cases pass.'),
}


class ScriptedModel:
    def __init__(self, api):
        self.mapping = {next(label[10:] for label in issue['fields']['labels'] if label.startswith('rr-source-')): key
                        for key, issue in api.issues.items()}
        self.api = api
        self.actions = self.plan()
        self.conversation_starts = 0

    def plan(self):
        yield 'discover', {}
        yield 'read_issue', {'key': self.mapping['MANIFEST']}
        yield 'declare_requirements', {'source_ids': sorted(CASES)}
        for sid, (decision, references, explanation) in CASES.items():
            yield 'read_issue', {'key': self.mapping[sid]}
            yield 'get_linked_issues', {'key': self.mapping[sid], 'depth': 3, 'limit': 40}
            refs = []
            for source, substring, stance in references:
                key = self.mapping[source]
                from release_agent.core import plain
                comment = next(c for c in self.api.bodies[key] if substring in plain(c['body']))
                refs.append({'key': key, 'comment_id': comment['id'], 'quote': substring, 'stance': stance})
                yield 'verify_evidence_scope', {'key': key, 'comment_id': comment['id']}
            row = {'source_id': sid, 'mandatory': True, 'decision': decision, 'explanation': explanation,
                   'outstanding': explanation if decision == 'INSUFFICIENT_EVIDENCE' else 'None', 'evidence': refs}
            yield 'submit_decision', {'report_json': json.dumps({'requirements': [row]})}

    def call(self, method, path, payload):
        if len(payload['input']) == 1:
            self.conversation_starts += 1
        name, args = next(self.actions)
        return {'id': 'scripted-offline', 'status': 'completed', 'model': 'scripted-test-double',
                'usage': {}, 'output': [{'type': 'function_call', 'call_id': name, 'name': name, 'arguments': json.dumps(args)}]}
