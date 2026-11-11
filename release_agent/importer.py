"""The only module permitted to read the supplied dataset."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from .core import API, Jira, adf, plain, safe, source


def validate_dataset(data):
    records = data['records']
    safe(data['dataset_label'])
    ids = [safe(r['source_id']) for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate source identifiers')
    for record in records:
        if record['kind'] not in ('manifest', 'requirement', 'work', 'evidence'):
            raise ValueError('Unknown record kind')
        if not all(isinstance(c, str) for c in record['comments']):
            raise ValueError('Comments must be strings')
        if set(record['links']) - set(ids):
            raise ValueError('Dangling source link')
    return records


def comment_text(record, index, comment):
    return f'Import comment {record["source_id"]}:{index + 1} sha256:{hashlib.sha256(comment.encode()).hexdigest()}' + '\n' + comment


def description_text(record):
    return (f'Source ID: {record["source_id"]}\nRecord kind: {record["kind"]}\n'
            f'Recorded status: {record["recorded_status"]}\nRecorded release: {record["release"]}\n'
            f'Source links: {json.dumps(record["links"])}\n'
            'Scenario actors/times below are fictional recorded facts; native Jira metadata identifies the importer.\n\n'
            + record['description'])


def parallel_apply(function, items, workers):
    if not 1 <= workers <= 8:
        raise ValueError('Import workers must be 1..8')
    if workers == 1:
        return [function(item) for item in items]
    pool = ThreadPoolExecutor(max_workers=workers)
    futures = [pool.submit(function, item) for item in items]
    try:
        return [future.result() for future in futures]
    finally:
        pool.shutdown(wait=True, cancel_futures=True)


def worker_jira(jira):
    if type(jira.api) is API:
        # Separate HTTP opener per task; no shared connection or authentication mutation.
        return Jira(jira.project, jira.scope, API(jira.api.base, jira.api.authorization,
                                               dict(jira.api.headers), jira.api.timeout))
    return jira  # In-memory protocol doubles, never a real transport.


def verify_import(jira, path, mapping=None, workers=1):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    records = validate_dataset(data)
    if jira.scope != data['dataset_label']:
        raise ValueError('Scope must equal dataset_label')
    if mapping is None:
        mapping = {}
        for issue in jira.search():
            sid = source(issue)
            if sid in mapping:
                raise ValueError('Duplicate source identity in live import audit')
            mapping[sid] = issue['key']
    if set(mapping) != {r['source_id'] for r in records}:
        raise ValueError('Imported issue identities differ from the supplied dataset')
    def check_record(record):
        client = worker_jira(jira)
        key = mapping[record['source_id']]
        issue = client.issue(key)
        if source(issue) != record['source_id']:
            raise ValueError('Source identity mismatch in import audit')
        if plain(issue['fields']['description']).rstrip() != description_text(record).rstrip():
            raise ValueError(f'{record["source_id"]}: imported description or source relationships changed')
        comments = [plain(c['body']).rstrip() for c in client.comments(key)]
        for index, text in enumerate(record['comments']):
            if comments.count(comment_text(record, index, text).rstrip()) != 1:
                raise ValueError(f'{record["source_id"]}: missing, changed or duplicate imported comment {index + 1}')
        native = {link.get('outwardIssue', link.get('inwardIssue', {})).get('key') for link in issue['fields'].get('issuelinks', [])}
        if any(mapping[sid] not in native for sid in record['links']):
            raise ValueError(f'{record["source_id"]}: missing native Jira dependency link')
        return len(record['comments'])
    total = sum(parallel_apply(check_record, records, workers))
    return {'issues': len(records), 'comments': total, 'verified': True,
            'input_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def import_dataset(jira, path, issue_type='Task', link_type='Relates', output='artifacts/import-map.json', workers=1):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    records = validate_dataset(data)
    if jira.scope != data['dataset_label']:
        raise ValueError('Scope must equal dataset_label')
    existing = jira.search()
    mapping = {}
    for issue in existing:
        sid = source(issue)
        if sid in mapping:
            raise ValueError(f'Duplicate imported source {sid}; resolve before retrying')
        mapping[sid] = issue['key']
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lock = Lock()
    completed = 0
    def import_record(record):
        nonlocal completed
        client = worker_jira(jira)
        sid = record['source_id']
        description = description_text(record)
        if sid not in mapping:
            created = client.api.call('POST', '/rest/api/3/issue', {'fields': {
                'project': {'key': jira.project}, 'issuetype': {'name': issue_type},
                'summary': f'[{sid}] {record["summary"]}', 'description': adf(description),
                'labels': [jira.scope, 'rr-' + record['kind'], 'rr-source-' + sid, 'rr-release-' + safe(record['release'])]}})
            with lock:
                mapping[sid] = created['key']
                # Convenience checkpoint only. Resume always reconstructs identity from Jira,
                # so even an interrupted local write cannot duplicate comments or lose provenance.
                output.write_text(json.dumps(mapping, indent=2), encoding='utf-8')
        key = mapping[sid]
        current = client.issue(key)
        if plain(current['fields']['description']).rstrip() != description.rstrip():
            raise ValueError(f'Imported description changed for {sid}; refusing silent overwrite')
        comments = client.comments(key)
        bodies = {plain(c['body']).rstrip() for c in comments}
        for index, comment in enumerate(record['comments']):
            # Include the ordinal: identical scenario comments must remain distinct.
            text = comment_text(record, index, comment)
            if text.rstrip() not in bodies:
                client.api.call('POST', f'/rest/api/3/issue/{key}/comment', {'body': adf(text)})
        with lock:
            completed += 1
            print(f'Imported {completed}/{len(records)} {sid} -> {key}', flush=True)
    parallel_apply(import_record, records, workers)
    linked_pairs = set()
    for record in records:
        if not record['links']:
            continue
        key = mapping[record['source_id']]
        current = jira.issue(key)
        existing_keys = {link.get('outwardIssue', link.get('inwardIssue', {})).get('key')
                         for link in current['fields'].get('issuelinks', [])}
        for sid in record['links']:
            other = mapping[sid]
            pair = tuple(sorted([key, other]))
            if other not in existing_keys and pair not in linked_pairs:
                jira.api.call('POST', '/rest/api/3/issueLink', {
                    'type': {'name': link_type}, 'inwardIssue': {'key': key}, 'outwardIssue': {'key': other}})
            linked_pairs.add(pair)
    output.write_text(json.dumps(mapping, indent=2), encoding='utf-8')
    audit = verify_import(jira, path, mapping, workers=workers)
    audit['links'] = len(linked_pairs)
    output.with_name('import-audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    return audit
