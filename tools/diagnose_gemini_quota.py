"""Read-only, single-request quota diagnostic. Never prints or saves credentials."""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from release_agent.core import NoRedirect, load_env, required, safe
from release_agent.providers import default_model


def main():
    load_env(ROOT / '.env')
    key = required('GEMINI_API_KEY')
    secrets = [os.getenv(name, '') for name in ('GEMINI_API_KEY', 'JIRA_API_TOKEN', 'OPENAI_API_KEY', 'DJANGO_SECRET_KEY') if os.getenv(name)]
    def redact(value):
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        for secret in secrets:
            text = text.replace(secret, '[REDACTED]').replace(quote(secret, safe=''), '[REDACTED]')
        text = re.sub(r'AIza[0-9A-Za-z_-]{20,}', '[REDACTED_API_KEY]', text)
        text = re.sub(r'ya29\.[0-9A-Za-z._-]+', '[REDACTED_ACCESS_TOKEN]', text)
        return text
    opener = build_opener(NoRedirect())
    model = safe(os.getenv('GEMINI_MODEL', '').strip() or 'gemini-3.8-flash')
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'configured_model': model,
              'endpoint': 'https://generativelanguage.googleapis.com/v1beta/interactions',
              'automatic_retries': 0, 'credentials_changed': False, 'project_settings_changed': False}
    payload = {'model': model, 'store': False, 'input': 'Call readiness_probe with nonce quota-diagnostic.',
               'tools': [{'type': 'function', 'name': 'readiness_probe', 'description': 'Read-only diagnostic.',
                          'parameters': {'type': 'object', 'properties': {'nonce': {'type': 'string'}}, 'required': ['nonce']}}],
               'generation_config': {'max_output_tokens': 512, 'thinking_level': 'low', 'tool_choice': 'any'}}
    request = Request(report['endpoint'], method='POST', data=json.dumps(payload).encode(), headers={
        'Content-Type': 'application/json', 'Accept': 'application/json', 'x-goog-api-key': key})
    try:
        with opener.open(request, timeout=120) as response:
            report.update({'http_status': response.status, 'currently_reproduced': False,
                           'response_body': response.read().decode('utf-8', errors='replace')})
    except HTTPError as exc:
        report.update({'http_status': exc.code, 'currently_reproduced': True,
                       'retry_after_seconds': exc.headers.get('Retry-After'),
                       'response_content_type': exc.headers.get('Content-Type'),
                       'response_body': exc.read().decode('utf-8', errors='replace')})
    except (URLError, TimeoutError):
        print('Network request failed; no response body captured and no credentials displayed.')
        return 1

    # This metadata lookup needs an already authenticated Cloud identity. Do not start login,
    # create credentials, alter gcloud configuration or print the access token.
    gcloud = shutil.which('gcloud')
    report['cloud_project_lookup'] = {'status': 'unavailable', 'reason': 'No authenticated Google Cloud CLI lookup available; an API key alone does not establish project identity.'}
    if gcloud:
        result = subprocess.run([gcloud, 'auth', 'print-access-token', '--quiet'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            token = result.stdout.strip()
            secrets.append(token)
            lookup = Request('https://apikeys.googleapis.com/v2/keys:lookupKey?' + urlencode({'keyString': key}),
                             headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
            try:
                with opener.open(lookup, timeout=30) as response:
                    metadata = json.loads(response.read())
                report['cloud_project_lookup'] = {'status': 'verified', 'parent': metadata.get('parent')}
            except HTTPError as exc:
                report['cloud_project_lookup'] = {'status': 'unavailable', 'http_status': exc.code,
                                                  'reason': 'Existing Cloud identity cannot perform the API key metadata lookup.'}
            except (URLError, TimeoutError, ValueError):
                report['cloud_project_lookup'] = {'status': 'unavailable', 'reason': 'Cloud metadata lookup failed; no project identity inferred.'}
    sanitized = json.loads(redact(report))
    output = ROOT / 'artifacts' / 'gemini-quota-diagnostic.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(sanitized, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
