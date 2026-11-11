import base64
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler


def load_env(path='.env'):
    if Path(path).exists():
        for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('\"').strip("'"))


def required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise ValueError(f'Set {name} in .env or the environment')
    return value


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class APIError(RuntimeError):
    def __init__(self, message, status, retry_after=None, reason=None, provider_message=None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after
        self.reason = reason
        self.provider_message = provider_message


class API:
    def __init__(self, base, authorization=None, headers=None, timeout=45):
        parsed = urlparse(base)
        if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
            raise ValueError('API base must be an HTTPS URL without credentials/query/fragment')
        self.base = base.rstrip('/')
        self.authorization = authorization
        self.headers = headers or {}
        self.timeout = timeout
        self.request_count = 0
        self.opener = build_opener(NoRedirect())

    def call(self, method, path, payload=None):
        if not path.startswith('/') or path.startswith('//'):
            raise ValueError('Only relative API paths permitted')
        data = None if payload is None else json.dumps(payload).encode()
        for attempt in range(4):
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json', **self.headers}
            if self.authorization:
                headers['Authorization'] = self.authorization
            req = Request(self.base + path, data=data, method=method, headers=headers)
            self.request_count += 1
            try:
                with self.opener.open(req, timeout=self.timeout) as response:
                    body = response.read()
                    return json.loads(body) if body else {}
            except HTTPError as exc:
                # Never automatically replay writes after an ambiguous server failure.
                header_delay = exc.headers.get('Retry-After', '')
                long_delay = header_delay.isdigit() and float(header_delay) > 15
                if (method == 'GET' or path == '/rest/api/3/search/jql') and exc.code in (429, 502, 503, 504) and attempt < 3 and not long_delay:
                    delay = exc.headers.get('Retry-After', '')
                    time.sleep(min(float(delay) if delay.isdigit() else 2 ** attempt, 15))
                    continue
                retry_after = exc.headers.get('Retry-After', '')
                retry_after = float(retry_after) if retry_after.replace('.', '', 1).isdigit() else None
                reason, provider_message = None, None
                try:
                    detail = json.loads(exc.read(16384)).get('error', {})
                    code = detail.get('status') or detail.get('code')
                    if isinstance(code, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', code):
                        reason = code
                    if isinstance(detail.get('message'), str):
                        provider_message = detail['message']
                        sensitive = [os.getenv(n) for n in ('GEMINI_API_KEY', 'GROQ_API_KEY', 'OPENAI_API_KEY', 'JIRA_API_TOKEN') if os.getenv(n)]
                        for name, value in headers.items():
                            if name.lower() in ('authorization', 'x-goog-api-key') and value:
                                sensitive.extend([value, value.split()[-1]])
                        for value in sensitive:
                            provider_message = provider_message.replace(value, '[REDACTED]')
                        provider_message = re.sub(r'AIza[0-9A-Za-z_-]{20,}', '[REDACTED_API_KEY]', provider_message)
                    if retry_after is None:
                        for item in detail.get('details', []):
                            value = item.get('retryDelay', '')
                            if isinstance(value, str) and re.fullmatch(r'\d+(?:\.\d+)?s', value):
                                retry_after = float(value[:-1])
                except (ValueError, TypeError, AttributeError):
                    pass
                message = f'API request failed: HTTP {exc.code}; {method} {path.split("?")[0]}'
                if provider_message:
                    message += '; ' + provider_message
                raise APIError(message, exc.code, retry_after, reason, provider_message) from None
            except URLError:
                raise RuntimeError('Network request failed; verify connectivity and API configuration') from None
            except TimeoutError:
                raise RuntimeError(f'API request timed out after {self.timeout:g}s during {method} {path.split("?")[0]}; '
                                   'no complete response received and the request was not automatically replayed') from None


def adf(text):
    return {'type': 'doc', 'version': 1, 'content': [
        {'type': 'paragraph', 'content': [{'type': 'text', 'text': line}]} if line else {'type': 'paragraph'}
        for line in text.split('\n')]}


def plain(node):
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ''
    if node.get('type') == 'text':
        return node.get('text', '')
    if node.get('type') == 'hardBreak':
        return '\n'
    text = ''.join(plain(x) for x in node.get('content', []))
    return text + ('\n' if node.get('type') in ('paragraph', 'heading', 'listItem') else '')


def safe(value):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
        raise ValueError('Invalid project, label, release or source identifier')
    return value


class Jira:
    def __init__(self, project, scope, api=None):
        self.project, self.scope = safe(project), safe(scope)
        if api is None:
            auth = base64.b64encode(f'{required("JIRA_EMAIL")}:{required("JIRA_API_TOKEN")}'.encode()).decode()
            api = API(required('JIRA_BASE_URL'), 'Basic ' + auth)
        self.api = api

    def search(self, extra=''):
        token, found = None, []
        for _ in range(100):
            payload = {'jql': f'project = "{self.project}" AND labels = "{self.scope}"' + extra,
                       'maxResults': 100, 'fields': ['summary', 'labels', 'description', 'issuelinks']}
            if token:
                payload['nextPageToken'] = token
            page = self.api.call('POST', '/rest/api/3/search/jql', payload)
            found.extend(page.get('issues', []))
            next_token = page.get('nextPageToken')
            if page.get('isLast') or not next_token:
                return found
            if token == next_token:
                raise RuntimeError('Jira search pagination did not advance')
            token = next_token
        raise RuntimeError('Search page bound exceeded')

    def comments(self, key):
        result, start = [], 0
        for _ in range(100):
            page = self.api.call('GET', f'/rest/api/3/issue/{safe(key)}/comment?' + urlencode({'startAt': start, 'maxResults': 100}))
            items = page.get('comments', [])
            result.extend(items)
            start += len(items)
            if start >= page['total']:
                return result
            if not items:
                raise RuntimeError('Incomplete comment pagination')
        raise RuntimeError('Comment page bound exceeded')

    def issue(self, key):
        issue = self.api.call('GET', f'/rest/api/3/issue/{safe(key)}?fields=summary,description,labels,issuelinks,project')
        fields = issue['fields']
        if fields['project']['key'] != self.project or self.scope not in fields.get('labels', []):
            raise ValueError('Issue is outside the configured import scope')
        return issue


def source(issue):
    labels = issue['fields'].get('labels', [])
    matches = [x[len('rr-source-'):] for x in labels if x.startswith('rr-source-')]
    if len(matches) != 1:
        raise ValueError(f'Invalid source identity on {issue["key"]}')
    return matches[0]


def aggregate(rows):
    mandatory = [r for r in rows if r['mandatory']]
    if not mandatory:
        raise ValueError('No mandatory requirements')
    if any(r['decision'] == 'FAIL' for r in mandatory):
        return 'BLOCKED'
    if any(r['decision'] == 'INSUFFICIENT_EVIDENCE' for r in mandatory):
        return 'NEEDS_REVIEW'
    return 'READY'
