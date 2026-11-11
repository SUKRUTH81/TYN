import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_agent.core import Jira,load_env,required
load_env()
jira=Jira(required('JIRA_PROJECT_KEY'),'tyn-release-assessment-v2')
mapping=json.loads(Path('artifacts/import-map.json').read_text())
last=jira.issue(mapping['REQ-12'])
links=last['fields'].get('issuelinks',[])
ready=any(link.get('outwardIssue',link.get('inwardIssue',{})).get('key')==mapping['REC-5957'] for link in links)
print(json.dumps({'all_issue_identities_allocated':len(mapping)==400,'last_dependency_link_ready':ready}))
