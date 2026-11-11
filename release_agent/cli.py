"""Submission-first command-line application using the Python standard library."""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from .core import APIError, Jira, load_env, required
from .providers import create_model_api, default_model


def main(argv=None):
    load_env()
    parser = argparse.ArgumentParser(description='TYN hybrid Jira release evidence investigator')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate-input', 'doctor', 'import', 'verify-import', 'assess', 'audit'):
        command = sub.add_parser(name)
        if name not in ('validate-input', 'audit'):
            command.add_argument('--project', default=os.getenv('JIRA_PROJECT_KEY'))
            command.add_argument('--scope', default='tyn-release-assessment-v2')
        if name in ('validate-input', 'import', 'verify-import'):
            command.add_argument('--dataset', default='inputs/dataset.json')
        if name in ('import', 'verify-import'):
            command.add_argument('--workers', type=int, default=4)
        if name in ('doctor', 'assess'):
            command.add_argument('--model', default=default_model())
        if name == 'doctor':
            checks = command.add_mutually_exclusive_group()
            checks.add_argument('--jira-only', action='store_true')
            checks.add_argument('--model-only', action='store_true')
        if name == 'import':
            command.add_argument('--issue-type', default='Task')
            command.add_argument('--link-type', default='Relates')
        if name == 'assess':
            command.add_argument('--release', default='R2.4')
            command.add_argument('--output', default='artifacts/live-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
            command.add_argument('--max-calls', type=int, default=180)
            command.add_argument('--max-seconds', type=int, default=1800)
            command.add_argument('--max-tokens', type=int, default=1000000)
            command.add_argument('--max-requirement-turns', type=int, default=12)
        if name == 'audit':
            command.add_argument('directory')
            command.add_argument('--reference', help='Optional independent expectations JSON; never sent to the agent')
    args = parser.parse_args(argv)
    try:
        if args.command == 'validate-input':
            from .importer import validate_dataset
            records = validate_dataset(json.loads(Path(args.dataset).read_text(encoding='utf-8')))
            print(json.dumps({'valid': True, 'issues': len(records), 'comments': sum(len(r['comments']) for r in records)}))
            return 0
        if args.command == 'audit':
            from .audit import audit_run
            result = audit_run(args.directory, args.reference)
            print(json.dumps(result, indent=2))
            return 0 if result['valid'] else 2
        model_only = args.command == 'doctor' and args.model_only
        if not args.project and not model_only:
            raise ValueError('Set JIRA_PROJECT_KEY or pass --project')
        jira = None if model_only else Jira(args.project, args.scope)
        if args.command == 'doctor':
            result = {}
            if not args.model_only:
                jira.api.call('GET', '/rest/api/3/myself')
                project = jira.api.call('GET', '/rest/api/3/project/' + jira.project)
                result = {'jira_project': project['key'], 'jira_connection': 'verified'}
            if not args.jira_only:
                from .agent import tool
                api = create_model_api(args.model)
                response = api.call('POST', '/v1/responses', {'model': args.model,
                    'instructions': 'Call readiness_probe with nonce configuration-check. This checks tool support only.',
                    'input': [{'role': 'user', 'content': 'Check native function calling.'}],
                    'tools': [tool('readiness_probe', 'Verify function calling.', {'nonce': {'type': 'string'}})],
                    'max_output_tokens': 1024, 'tool_choice': 'required', 'parallel_tool_calls': False, 'store': False})
                calls = [c for c in response.get('output', []) if c.get('type') == 'function_call']
                if response.get('status') != 'completed' or not any(c.get('name') == 'readiness_probe' for c in calls):
                    raise RuntimeError('Model connection did not return a usable probe tool call')
                result.update({'model_connection': 'verified', 'requested_model': args.model,
                               'actual_model': response.get('model'), 'response_id': response.get('id'), 'usage': response.get('usage')})
            print(json.dumps(result, indent=2))
        elif args.command == 'import':
            from .importer import import_dataset
            print(json.dumps(import_dataset(jira, args.dataset, args.issue_type, args.link_type, workers=args.workers), indent=2))
        elif args.command == 'verify-import':
            from .importer import verify_import
            print(json.dumps(verify_import(jira, args.dataset, workers=args.workers), indent=2))
        elif args.command == 'assess':
            from .agent import run
            if min(args.max_calls, args.max_seconds, args.max_tokens, args.max_requirement_turns) <= 0:
                raise ValueError('Budgets must be positive')
            report = run(jira, args.release, args.output, args.model, args.max_calls, args.max_seconds, args.max_tokens,
                         max_requirement_turns=args.max_requirement_turns)
            print(f'{report["overall_decision"]}: {args.output}/report.md')
            return 0 if report['assessment_complete'] else 2
        return 0
    except (ValueError, RuntimeError, KeyError, OSError) as exc:
        # Provider/network errors deliberately omit request bodies and authorization values.
        text = str(exc)
        for key in ('JIRA_API_TOKEN', 'GEMINI_API_KEY', 'GROQ_API_KEY', 'OPENAI_API_KEY'):
            secret = os.getenv(key)
            if secret:
                text = text.replace(secret, '[redacted]')
        print('ERROR: ' + text)
        if isinstance(exc, APIError):
            print(json.dumps({'http_status': exc.status, 'reason': exc.reason, 'message': exc.provider_message,
                              'retry_after_seconds': exc.retry_after}))
        return 1
