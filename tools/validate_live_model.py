"""Actual model + offline Jira protocol double. NEVER a live Jira submission run."""
import contextlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from release_agent.agent import run
from release_agent.core import Jira, load_env
from release_agent.importer import import_dataset
from release_agent.providers import default_model
from tests.test_agent import FakeAPI


def main():
    load_env(ROOT / '.env')
    output = ROOT / 'artifacts' / ('live-model-validation-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    api = FakeAPI()
    jira = Jira('TEST', 'tyn-release-assessment-v2', api)
    with contextlib.redirect_stdout(io.StringIO()):
        import_dataset(jira, ROOT / 'inputs/dataset.json', output=output / 'import-map.json')
    print('LIVE MODEL, OFFLINE JIRA VALIDATION ONLY. Not a real Jira assessment.', flush=True)
    print('Artifacts: ' + str(output), flush=True)
    report = run(jira, 'R2.4', output, default_model(), max_calls=120, max_seconds=480, max_tokens=350000,
                 provenance='live_model_offline_jira')
    print(json.dumps({'overall': report['overall_decision'], 'complete': report['assessment_complete']}), flush=True)
    return 0 if report['assessment_complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
