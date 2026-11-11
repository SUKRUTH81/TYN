"""Reproducible scripted pipeline demonstration; never a live submission report."""
import contextlib
import io
import sys
import argparse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from release_agent.agent import run
from release_agent.audit import audit_run
from release_agent.core import Jira
from release_agent.importer import import_dataset
from tests.test_agent import FakeAPI
from tests.hybrid_fixture import ScriptedModel

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', default='artifacts/offline-pipeline-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
options = parser.parse_args()
output = (ROOT / options.output).resolve()
if not output.is_relative_to((ROOT / 'artifacts').resolve()):
    parser.error('Demo output must be under artifacts/')
api = FakeAPI()
jira = Jira('TEST', 'tyn-release-assessment-v2', api)
with contextlib.redirect_stdout(io.StringIO()):
    import_dataset(jira, ROOT / 'inputs/dataset.json', output=output / 'import-map.json')
print('OFFLINE TEST DOUBLE: scripted model and in-memory Jira; not live evidence.')
run(jira, 'R2.4', output, 'scripted-test-double', model_api=ScriptedModel(api), provenance='offline_test_double')
result = audit_run(output, ROOT / 'tests' / 'expected_decisions.json')
print(result)
raise SystemExit(0 if result['valid'] else 2)
