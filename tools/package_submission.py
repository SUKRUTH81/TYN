"""Allowlisted assessment packaging; source-only and real-live artifacts stay distinct."""
import argparse
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from release_agent.audit import audit_run

parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--run')
mode.add_argument('--source-only', action='store_true')
args = parser.parse_args()
run = (root / args.run).resolve() if args.run else None
artifacts = ['report.md', 'report.html', 'report.json', 'trace.jsonl', 'metrics.json']
if run:
    if not run.is_relative_to((root / 'artifacts').resolve()):
        parser.error('Run must be under artifacts/')
    audit = audit_run(run)
    if not audit['valid'] or audit.get('provenance') != 'live_jira':
        parser.error('Only an audited completed LIVE JIRA run can be submitted: ' + str(audit))
    if not all((run / name).is_file() for name in artifacts):
        parser.error('Run is missing required artifacts')

destination = root / ('tyn-cli-source.zip' if args.source_only else 'submission.zip')
with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
    def add(file):
        archive.write(file, file.relative_to(root).as_posix())
    for name in ['README.md', 'RUN_STATUS.md', 'requirements.txt', '.env.example', '.gitignore', 'assessment.txt', 'run_assessment.ps1']:
        file = root / name
        if file.is_file():
            add(file)
    for folder, suffixes in [('release_agent', {'.py'}), ('tests', {'.py', '.json'}), ('docs', {'.md'}),
                             ('inputs', {'.json', '.pdf'}), ('.github', {'.yml'})]:
        for file in sorted((root / folder).rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix in suffixes:
                add(file)
    for name in ['package_submission.py', 'offline_demo.py', 'validate_live_model.py',
                 'diagnose_gemini_connection.py', 'diagnose_gemini_quota.py', 'check_jira_requirements.py']:
        add(root / 'tools' / name)
    import_audit = root / 'artifacts' / 'import-audit.json'
    if import_audit.is_file() and not run:
        archive.write(import_audit, 'validation/live-import-audit.json')
    if run:
        for name in artifacts:
            archive.write(run / name, 'artifacts/live-run/' + name)
        if (run / 'trace.md').is_file():
            archive.write(run / 'trace.md', 'artifacts/live-run/trace.md')
        import_audit = root / 'artifacts' / 'import-audit.json'
        if import_audit.is_file():
            archive.write(import_audit, 'artifacts/import-audit.json')
print(destination)
