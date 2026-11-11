"""Read-only live verification of manifest-linked requirement identities and links."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from release_agent.core import Jira, load_env, required, source, plain
from release_agent.evidence import source_links

load_env(ROOT / '.env')
jira = Jira(required('JIRA_PROJECT_KEY'), 'tyn-release-assessment-v2')
hits = jira.search(' AND labels = "rr-release-R2.4" AND labels in ("rr-manifest", "rr-requirement")')
manifest = [item for item in hits if 'rr-manifest' in item['fields']['labels']]
requirements = {source(item): item for item in hits if 'rr-requirement' in item['fields']['labels']}
rows = []
for sid, item in sorted(requirements.items()):
    record = jira.issue(item['key'])
    declared = source_links(plain(record['fields']['description']))
    native = record['fields'].get('issuelinks', [])
    linked_sources = set()
    for link in native:
        other = link.get('outwardIssue', link.get('inwardIssue', {}))
        if other.get('key'):
            linked_sources.add(source(jira.issue(other['key'])))
    rows.append({'source_id': sid, 'jira_key': item['key'], 'summary': record['fields']['summary'],
                 'url': jira.api.base + '/browse/' + item['key'],
                 'declared_evidence_sources': declared, 'all_declared_links_present': set(declared) <= linked_sources})
declared_requirements = source_links(plain(manifest[0]['fields']['description'])) if len(manifest) == 1 else []
report = {'project': jira.project, 'scope': jira.scope, 'manifest_key': manifest[0]['key'] if len(manifest) == 1 else None,
          'requirement_count': len(rows), 'exact_manifest_coverage': set(declared_requirements) == set(requirements),
          'requirements': rows}
output = ROOT / 'artifacts' / 'jira-requirements-check.json'
output.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
