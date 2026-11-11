"""Bounded endpoint comparison; no automatic retries or credential changes."""
import json
import argparse
import os
import re
import sys
import time
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from release_agent.core import NoRedirect, load_env, required, safe
from release_agent.providers import default_model


def transport_stage(metrics):
    """Describe observations, without attributing an upstream timeout to billing."""
    if metrics.get('time_starttransfer', 0) > 0:
        return 'response_started'
    if metrics.get('size_upload', 0) > 0 and metrics.get('time_appconnect', 0) > 0:
        return 'tls_complete_request_uploaded_waiting_for_response'
    if metrics.get('time_appconnect', 0) > 0:
        return 'tls_complete'
    if metrics.get('time_connect', 0) > 0:
        return 'tcp_connected'
    if metrics.get('time_namelookup', 0) > 0:
        return 'dns_complete'
    return 'connection_not_established'


def classify_results(results):
    generation = [r for r in results if r['operation'] not in ('model_metadata', 'count_tokens', 'count_tokens_curl')]
    if not generation:
        return {'classification': 'generation_not_tested', 'confirmed_cause': None,
                'explanation': 'Metadata does not establish generation eligibility, billing status or usable quota.'}
    statuses = [r.get('http_status') for r in generation]
    if any(r.get('http_status') == 200 and r.get('response_complete', True) for r in generation):
        return {'classification': 'generation_http_success', 'confirmed_cause': None,
                'explanation': 'A generation endpoint responded; inspect the body for a usable function call before running assessment.'}
    if 429 in statuses:
        return {'classification': 'quota_or_rate_limit', 'confirmed_cause': 'HTTP 429',
                'explanation': 'Read the complete error body to distinguish RPM, TPM, daily limits and other quota restrictions.'}
    if 503 in statuses:
        return {'classification': 'provider_unavailable', 'confirmed_cause': 'HTTP 503',
                'explanation': 'A service-unavailable response was received. Consult its message and Retry-After.'}
    if any(s in (401, 403) for s in statuses):
        return {'classification': 'access_rejected', 'confirmed_cause': 'HTTP 401/403',
                'explanation': 'Inspect the provider message for key, permissions, project eligibility or billing restrictions.'}
    if all(r.get('http_status') is None or r.get('response_complete') is False for r in generation):
        return {'classification': 'generation_response_missing', 'confirmed_cause': None,
                'explanation': 'No complete HTTP response. A timeout alone cannot distinguish network/proxy delay from provider delay.'}
    return {'classification': 'other_http_error', 'confirmed_cause': None,
            'explanation': 'Inspect endpoint status and response body; do not infer a quota or billing cause.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--metadata-only', action='store_true', help='Skip all generation requests.')
    mode.add_argument('--basic', action='store_true', help='Test token counting and plain text before testing tools.')
    parser.add_argument('--timeout', type=int, default=20, choices=range(5, 61), metavar='5..60')
    options = parser.parse_args()
    load_env(ROOT / '.env')
    model, key = safe(os.getenv('GEMINI_MODEL', '').strip() or 'gemini-3.8-flash'), required('GEMINI_API_KEY')
    secrets = [os.getenv(n) for n in ('GEMINI_API_KEY', 'GROQ_API_KEY', 'OPENAI_API_KEY', 'JIRA_API_TOKEN') if os.getenv(n)]
    opener = build_opener(NoRedirect())
    results = []
    def publish(item, start):
        item['elapsed_seconds'] = round(time.monotonic() - start, 3)
        encoded = json.dumps(item)
        for secret in secrets:
            encoded = encoded.replace(secret, '[REDACTED]')
        encoded = re.sub(r'AIza[0-9A-Za-z_-]{20,}', '[REDACTED_API_KEY]', encoded)
        encoded = re.sub(r'(https?://)[^/\s@]+@', r'\1[REDACTED]@', encoded)
        item = json.loads(encoded)
        results.append(item)
        print(json.dumps(item), flush=True)
        return item
    def check(name, path, payload=None):
        print(f'Checking {name} ({options.timeout}-second timeout, no retries)...', flush=True)
        start = time.monotonic()
        headers = {'x-goog-api-key': key, 'Accept': 'application/json', 'Content-Type': 'application/json'}
        request = Request('https://generativelanguage.googleapis.com' + path, headers=headers,
                          data=json.dumps(payload).encode() if payload is not None else None)
        try:
            with opener.open(request, timeout=options.timeout) as response:
                item = {'operation': name, 'http_status': response.status, 'body': response.read().decode('utf-8', errors='replace')}
        except HTTPError as exc:
            item = {'operation': name, 'http_status': exc.code, 'retry_after': exc.headers.get('Retry-After'),
                    'body': exc.read().decode('utf-8', errors='replace')}
        except (URLError, TimeoutError) as exc:
            item = {'operation': name, 'http_status': None, 'error_type': type(exc).__name__, 'error': str(exc)}
        return publish(item, start)
    def compare_with_curl(operation, path, payload):
        executable = shutil.which('curl.exe') or shutil.which('curl')
        if not executable:
            return
        print('Comparing ' + operation + ' with curl (same proxy settings; key passed through stdin)...', flush=True)
        config = '\n'.join([
            'url = ' + json.dumps('https://generativelanguage.googleapis.com' + path),
            'header = ' + json.dumps('x-goog-api-key: ' + key),
            'header = "Content-Type: application/json"',
            'data-binary = ' + json.dumps(json.dumps(payload)),
            f'max-time = {options.timeout}', 'connect-timeout = 10', 'silent', 'show-error',
            'write-out = "\\n__CURL_DIAG__%{json}"',
        ])
        start = time.monotonic()
        try:
            response = subprocess.run([executable, '--config', '-'], input=config, capture_output=True,
                                      text=True, timeout=options.timeout + 5)
            body, _, raw_metrics = response.stdout.rpartition('\n__CURL_DIAG__')
            metrics = json.loads(raw_metrics)
            timing = {name: metrics.get(name, 0) for name in (
                'time_namelookup', 'time_connect', 'time_appconnect', 'time_pretransfer',
                'time_starttransfer', 'time_total', 'size_upload', 'size_download', 'http_connect', 'ssl_verify_result')}
            publish({'operation': operation, 'http_status': metrics.get('http_code') or None,
                     'transport_metrics': timing, 'last_observed_stage': transport_stage(timing),
                     'response_complete': response.returncode == 0,
                     'body': body, 'curl_exit_code': response.returncode, 'transport_error': response.stderr}, start)
        except subprocess.TimeoutExpired:
            publish({'operation': operation, 'http_status': None, 'error_type': 'TimeoutExpired'}, start)
    declaration = {'name': 'readiness_probe', 'description': 'Check native function calling.',
                   'parameters': {'type': 'object', 'properties': {'nonce': {'type': 'string'}}, 'required': ['nonce']}}
    metadata = check('model_metadata', '/v1beta/models/' + model)
    if options.metadata_only or metadata.get('http_status') in (400, 401, 403, 404, 429) or metadata.get('error_type') == 'URLError':
        pass
    elif options.basic:
        payload = {'contents': [{'parts': [{'text': 'Hello'}]}]}
        count = check('count_tokens', '/v1beta/models/' + model + ':countTokens', payload)
        if count.get('http_status') is None:
            compare_with_curl('count_tokens_curl', '/v1beta/models/' + model + ':countTokens', payload)
        if count.get('http_status') not in (400, 401, 403, 404, 429):
            plain_payload = {
                'contents': [{'parts': [{'text': 'Reply only OK.'}]}],
                'generationConfig': {'maxOutputTokens': 256, 'thinkingConfig': {'thinkingLevel': 'LOW'}}}
            plain = check('plain_text_generation', '/v1beta/models/' + model + ':generateContent', plain_payload)
            if plain.get('http_status') is None:
                compare_with_curl('plain_text_generation_curl', '/v1beta/models/' + model + ':generateContent', plain_payload)
    else:
        probe = check('interactions_function_probe', '/v1beta/interactions', {
            'model': model, 'store': False, 'input': 'Call readiness_probe with nonce connection-check.',
            'tools': [{'type': 'function', **declaration}],
            'generation_config': {'max_output_tokens': 256, 'thinking_level': 'low', 'tool_choice': 'any'}})
        if probe.get('http_status') is None or probe.get('http_status', 0) >= 500:
            check('generate_content_function_probe', '/v1beta/models/' + model + ':generateContent', {
                'contents': [{'role': 'user', 'parts': [{'text': 'Call readiness_probe with nonce connection-check.'}]}],
                'tools': [{'functionDeclarations': [declaration]}],
                'toolConfig': {'functionCallingConfig': {'mode': 'ANY'}},
                'generationConfig': {'maxOutputTokens': 256, 'thinkingConfig': {'thinkingLevel': 'LOW'}}})
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'model': model,
              'credentials_changed': False, 'proxy_variables_present': [n for n in ('HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY', 'NO_PROXY') if os.getenv(n)],
              'summary': classify_results(results), 'results': results}
    filename = 'gemini-metadata-diagnostic.json' if options.metadata_only else 'gemini-basic-diagnostic.json' if options.basic else 'gemini-connection-diagnostic.json'
    output = ROOT / 'artifacts' / filename
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report['summary']), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
