"""Post-run integrity checks. Never invoked by the model or used to alter decisions."""
import hashlib
import json
from pathlib import Path
from .core import aggregate


def audit_run(directory, reference=None):
    root = Path(directory)
    errors = []
    try:
        report = json.loads((root / 'report.json').read_text(encoding='utf-8'))
        metrics = json.loads((root / 'metrics.json').read_text(encoding='utf-8'))
        trace = (root / 'trace.jsonl').read_bytes()
        events = [json.loads(line) for line in trace.decode('utf-8').splitlines() if line]
        rows = report['requirements']
        ids = [r['source_id'] for r in rows]
        if not ids or len(ids) != len(set(ids)):
            errors.append('Missing or duplicate requirement identities')
        if report['overall_decision'] != aggregate(rows):
            errors.append('Overall decision disagrees with mandatory requirement decisions')
        if not report.get('assessment_complete') or any(r.get('assessment_status') != 'COMPLETE' for r in rows):
            errors.append('Assessment is partial or contains tooling failures')
        if metrics.get('status') != 'COMPLETED':
            errors.append('Metrics do not claim a completed investigation')
        if metrics.get('trace_sha256') != hashlib.sha256(trace).hexdigest():
            errors.append('Trace digest mismatch')
        if report.get('provenance') != metrics.get('provenance'):
            errors.append('Report and metrics provenance disagree')
        submitted = {e.get('session'): e['result'] for e in events if e.get('event') == 'tool_call'
                     and e.get('name') == 'submit_decision' and 'error' not in e.get('result', {})}
        for row in rows:
            accepted = submitted.get(row['source_id'])
            if not accepted or accepted.get('decision') != row['decision'] or accepted.get('evidence') != row['evidence']:
                errors.append(f'{row["source_id"]}: report does not match a validated traced submission')
        if set(submitted) != set(ids):
            errors.append('Traced submissions and report coverage differ')
        declarations = [e['result'].get('source_ids') for e in events if e.get('event') == 'tool_call'
                        and e.get('name') == 'declare_requirements' and e.get('result', {}).get('accepted')]
        if not declarations or set(declarations[-1]) != set(ids):
            errors.append('Report coverage differs from the validated manifest declaration')
        if reference:
            expected = json.loads(Path(reference).read_text(encoding='utf-8'))
            decisions = {r['source_id']: r['decision'] for r in rows}
            if decisions != expected['decisions'] or report['overall_decision'] != expected['overall_decision']:
                errors.append('Independent reference audit mismatch; inspect the report, never overwrite model decisions')
        return {'valid': not errors, 'errors': errors, 'provenance': report.get('provenance'), 'requirements': len(rows)}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return {'valid': False, 'errors': ['Cannot audit run: ' + str(exc)]}
