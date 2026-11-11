"""Conservative, inspectable evidence checks; no source IDs or answer key."""
import json
import re
from datetime import datetime
from decimal import Decimal


HEADER = re.compile(r'^Recorded event (?P<recorded_at>\S+)\s*\| actor (?P<actor>.+?)\s*\| role (?P<role>[^\n]+)$', re.M)
SCOPES = {
    'release': r'\brelease\s+(R\d+(?:\.\d+)*)\b',
    'commit': r'\bcommit\s+([a-f0-9]{7,40})\b',
    'service': r'\bservice\s+([\w-]+)',
    'environment': r'\benvironment\s+([\w-]+)',
    'prompt': r'\bprompt(?:\s+bundle)?\s+(p\d+)\b',
}
INJECTION = re.compile(r'automated.{0,25}(review|assess|agent)|ignore\s+(?:all\s+)?(?:previous|prior)|'
                       r'do not (?:mention|disclose|report)|system prompt|report\s+REQ-\d+\s+as\s+PASS', re.I)
ROUTINE = re.compile(r'^(?:Picked this up\.|Discussed in the handover call;|Tracking for the release checklist\.|'
                     r'Reminder: please keep results in this ticket|Status updated\.|Linked the related work so|'
                     r'Streaming investigation note\s+\d+\b)', re.I)


def parse_comment(text):
    match = HEADER.search(text)
    meta = match.groupdict() if match else {'recorded_at': None, 'actor': None, 'role': None}
    body = text[match.end():].strip() if match else text.strip()
    valid_time = False
    if meta['recorded_at']:
        try:
            valid_time = datetime.fromisoformat(meta['recorded_at']).tzinfo is not None
        except ValueError:
            pass
    return {**meta, 'body': body, 'valid_recorded_time': valid_time, 'injection_suspected': bool(INJECTION.search(body))}


def stated_scope(text):
    result = {key: sorted({m.lower() for m in re.findall(pattern, text, re.I)}) for key, pattern in SCOPES.items()}
    environments = re.findall(r'Approval scope:\s*([\w-]+)|\bfor\s+(production|staging)\b', text, re.I)
    result['environment'] = sorted(set(result['environment']) | {v.lower() for pair in environments for v in pair if v})
    return result


def scope_check(text, target):
    found = stated_scope(text)
    # Exact commit equality is intentional: no guessed equivalence of ambiguous SHAs.
    return {key: {'expected': target.get(key), 'found': values,
                  'status': 'not_stated' if not values else 'match' if values == [str(target.get(key, '')).lower()] else 'mismatch'}
            for key, values in found.items()}


def applicable(text, target, prompt=False):
    checks = scope_check(text, target)
    keys = ['release', 'commit', 'service', 'environment'] + (['prompt'] if prompt else [])
    return all(checks[k]['status'] == 'match' for k in keys) and checks['prompt']['status'] != 'mismatch'


def source_links(description):
    match = re.search(r'^Source links: (.+)$', description, re.M)
    if not match:
        raise ValueError('Imported source relationship header is missing')
    value = json.loads(match[1])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError('Invalid source relationship header')
    return value


def target_from(description):
    match = re.search(r'^Target:\s*(\{.+\})\s*$', description, re.M)
    if not match:
        raise ValueError('Manifest has no explicit target object')
    target = json.loads(match[1])
    if not all(isinstance(target.get(k), str) and target[k] for k in SCOPES):
        raise ValueError('Manifest target is incomplete')
    return target


def criterion_from(description):
    match = re.search(r'Acceptance criterion:\s*(.+)', description, re.S)
    return match[1].strip() if match else description


def authority(meta, criterion):
    role = (meta['role'] or '').lower()
    if not meta['valid_recorded_time'] or meta['injection_suspected']:
        return False
    if re.search(r'Security Owner', criterion, re.I):
        name = re.search(r'Security Owner\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', criterion)
        return role == 'security owner' and (not name or (meta['actor'] or '').lower() == name[1].lower())
    return bool(re.search(r'\bqa\b', role))


def outcome_signals(text, criterion):
    """Recognize explicit outcomes only; unknown language is not automatic proof."""
    passed = bool(re.search(r'\bapproved\b|no data loss observed|\bPASS\b', text, re.I))
    failed = bool(re.search(r'\bFAIL(?:ED)?\b|reopening defect|\bunredacted\b|duplicated final|records[^.]*\blost\b', text, re.I))
    open_defect = bool(re.search(r'defect[^.]*status:\s*open|reopening defect', text, re.I))
    for a, b in re.findall(r'\b(\d+) of (\d+)\b', text):
        passed |= int(a) == int(b) and int(b) > 0
        failed |= int(a) < int(b)
    cost_limit = re.search(r'at most USD\s*([\d.]+)', criterion, re.I)
    cost = re.search(r'Mean cost USD\s*([\d.]+)', text, re.I)
    latency_limit = re.search(r'at most\s*([\d.]+) seconds', criterion, re.I)
    latency = re.search(r'p95 (?:latency|response time)\s*([\d.]+) seconds', text, re.I)
    for limit, value in ((cost_limit, cost), (latency_limit, latency)):
        if limit and value:
            passed, failed = Decimal(value[1]) <= Decimal(limit[1]), Decimal(value[1]) > Decimal(limit[1])
    quality_limit = re.search(r'at least\s*([\d.]+) percent', criterion, re.I)
    quality = re.search(r'(?:accuracy|score)\s*([\d.]+) percent', text, re.I)
    if quality_limit and quality:
        passed, failed = Decimal(quality[1]) >= Decimal(quality_limit[1]), Decimal(quality[1]) < Decimal(quality_limit[1])
    return {'pass': passed and not failed, 'fail': failed, 'open_confirmed_defect': open_defect}


def run_ids(text):
    return set(re.findall(r'\b[A-Z][A-Z0-9]+(?:-DEF)?-\d+\b', text))


def superseded_by(old, new):
    """A later, same-role recorded retest must explicitly name the old run."""
    named = set(re.findall(r'\bsupersedes\s+([A-Z][A-Z0-9]+(?:-DEF)?-\d+)', new['body'], re.I))
    try:
        later = datetime.fromisoformat(new['recorded_at']) > datetime.fromisoformat(old['recorded_at'])
    except (ValueError, TypeError):
        return False
    return later and old['role'] == new['role'] and bool(named & run_ids(old['body']))
