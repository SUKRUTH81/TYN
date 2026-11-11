"""Normalize native Gemini tool calls for the bounded investigator loop."""
import json
import os
import time
from .core import API, APIError, required, safe


DEFAULT_MODEL = 'gemini-3.8-flash'


def default_model():
    provider = os.getenv('MODEL_PROVIDER', 'gemini').strip().lower()
    if provider == 'groq':
        return 'groq/' + (os.getenv('GROQ_MODEL', '').strip() or 'openai/gpt-oss-120b')
    if provider not in ('gemini', 'openai'):
        raise ValueError('MODEL_PROVIDER must be gemini, groq or openai')
    if provider == 'openai':
        return os.getenv('OPENAI_MODEL', '').strip() or 'gpt-5.4'
    return os.getenv('GEMINI_MODEL', '').strip() or DEFAULT_MODEL


def model_key_name(model):
    if model.startswith('groq/'):
        return 'GROQ_API_KEY'
    return 'GEMINI_API_KEY' if model.startswith('gemini-') else 'OPENAI_API_KEY'


def model_provider(model):
    if model.startswith('groq/'):
        return 'groq'
    return 'gemini' if model.startswith('gemini-') else 'openai'


class GeminiAPI:
    def __init__(self, transport=None):
        timeout = float(os.getenv('MODEL_TIMEOUT_SECONDS', '120'))
        if not 1 <= timeout <= 180:
            raise ValueError('MODEL_TIMEOUT_SECONDS must be 1..180')
        self.transport = transport or API('https://generativelanguage.googleapis.com',
                                         headers={'x-goog-api-key': required('GEMINI_API_KEY')}, timeout=timeout)
        rpm = float(os.getenv('GEMINI_RPM', '8'))
        if not 0 <= rpm <= 600:
            raise ValueError('GEMINI_RPM must be 0..600 (0 disables pacing)')
        self.interval = 60 / rpm if rpm and transport is None else 0
        self.last_request = None

    def send(self, payload):
        for attempt in range(3):
            if self.last_request is not None and self.interval:
                time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                return self.transport.call('POST', '/v1beta/interactions', payload), attempt
            except APIError as exc:
                if exc.status != 429 or attempt == 2:
                    raise
                # 429 explicitly rejects the request. Never replay timeouts or ambiguous 5xx failures.
                if exc.retry_after is not None and exc.retry_after > 60:
                    raise  # Do not violate a long Retry-After or block this bounded run indefinitely.
                time.sleep(exc.retry_after if exc.retry_after is not None else 15 * (attempt + 1))

    def call(self, method, path, payload):
        # The investigator uses one internal tool protocol; no OpenAI request is sent.
        if method != 'POST' or path != '/v1/responses':
            raise ValueError('Unsupported model operation')
        history, names = [], {}
        for item in payload['input']:
            kind = item.get('type')
            if item.get('role') == 'user':
                history.append({'type': 'user_input', 'content': [{'type': 'text', 'text': item['content']}]})
            elif kind == 'provider_step':
                # Preserve opaque thought signatures and all returned steps verbatim.
                history.append(item['step'])
            elif kind == 'function_call':
                names[item['call_id']] = item['name']
            elif kind == 'function_call_output':
                history.append({'type': 'function_result', 'name': names[item['call_id']],
                                'call_id': item['call_id'], 'result': [{'type': 'text', 'text': item['output']}]})
            else:
                raise ValueError('Unsupported Gemini history item')
        tools = [{key: value for key, value in tool.items() if key in ('type', 'name', 'description', 'parameters')}
                 for tool in payload['tools']]
        thinking = os.getenv('GEMINI_THINKING_LEVEL', 'medium').strip() or 'medium'
        if thinking not in ('low', 'medium', 'high'):
            raise ValueError('GEMINI_THINKING_LEVEL must be low, medium or high')
        raw, retries = self.send({
            'model': safe(payload['model']), 'store': False, 'input': history,
            'system_instruction': payload['instructions'], 'tools': tools,
            'generation_config': {'tool_choice': {'allowed_tools': {'mode': 'any', 'tools': [t['name'] for t in tools]}},
                                  'thinking_level': thinking, 'max_output_tokens': payload['max_output_tokens']}})
        output, calls = [], []
        for step in raw.get('steps', []):
            output.append({'type': 'provider_step', 'step': step})
            if step.get('type') == 'function_call':
                call_id, name = step.get('id'), step.get('name')
                if not isinstance(call_id, str) or not call_id or not isinstance(name, str) or not name:
                    raise RuntimeError('Gemini returned a function call without a valid ID/name')
                arguments = step.get('arguments', {})
                calls.append({'type': 'function_call', 'call_id': call_id, 'name': name,
                              'arguments': arguments if isinstance(arguments, str) else json.dumps(arguments)})
        output.extend(calls)
        usage = raw.get('usage') or {}
        normalized = {target: usage[source] for target, source in {
            'input_tokens': 'total_input_tokens', 'output_tokens': 'total_output_tokens',
            'total_tokens': 'total_tokens', 'reasoning_tokens': 'total_thought_tokens',
            'cached_input_tokens': 'total_cached_tokens', 'tool_use_input_tokens': 'total_tool_use_tokens',
        }.items() if source in usage}
        status = raw.get('status')
        if status == 'requires_action' and calls:
            status = 'completed'  # A complete tool-selection turn, not a completed investigation.
        return {'id': raw.get('id'), 'model': raw.get('model', payload['model']), 'status': status or 'failed',
                'usage': normalized, 'output': output, 'provider': 'gemini', 'provider_response': raw,
                'rate_limit_retries': retries}


class GroqAPI:
    """Translate the investigator protocol into Groq local chat tool calling."""

    def __init__(self, transport=None):
        timeout = float(os.getenv('MODEL_TIMEOUT_SECONDS', '120'))
        if not 1 <= timeout <= 180:
            raise ValueError('MODEL_TIMEOUT_SECONDS must be 1..180')
        self.transport = transport or API('https://api.groq.com',
            'Bearer ' + required('GROQ_API_KEY'),
            headers={'User-Agent': 'TYN-Release-Evidence-Agent/1.0'}, timeout=timeout)

    def send(self, payload):
        for attempt in range(3):
            try:
                return self.transport.call('POST', '/openai/v1/chat/completions', payload), attempt
            except APIError as exc:
                # Only retry explicit rejection, with a bounded provider-specified wait.
                if exc.status != 429 or attempt == 2 or exc.retry_after is None or not 0 <= exc.retry_after <= 60:
                    raise
                time.sleep(exc.retry_after)

    def call(self, method, path, payload):
        if method != 'POST' or path != '/v1/responses':
            raise ValueError('Unsupported model operation')
        messages = [{'role': 'system', 'content': payload['instructions']}]
        for item in payload['input']:
            if item.get('role') == 'user':
                messages.append({'role': 'user', 'content': item['content']})
            elif item.get('type') == 'function_call':
                call = {'id': item['call_id'], 'type': 'function', 'function': {
                    'name': item['name'], 'arguments': item['arguments']}}
                if messages[-1].get('role') != 'assistant':
                    messages.append({'role': 'assistant', 'content': None, 'tool_calls': []})
                messages[-1]['tool_calls'].append(call)
            elif item.get('type') == 'function_call_output':
                messages.append({'role': 'tool', 'tool_call_id': item['call_id'], 'content': item['output']})
            else:
                raise ValueError('Unsupported Groq history item')
        tools = [{'type': 'function', 'function': {k: t[k] for k in ('name', 'description', 'parameters')}}
                 for t in payload['tools']]
        request = {
            'model': payload['model'].removeprefix('groq/'), 'messages': messages, 'tools': tools,
            'tool_choice': 'required', 'parallel_tool_calls': False,
            'max_completion_tokens': payload['max_output_tokens']}
        recoveries = 0
        try:
            raw, retries = self.send(request)
        except APIError as exc:
            if exc.status != 400 or exc.reason != 'tool_use_failed':
                raise
            # Explicitly rejected generation, not an ambiguous transport failure.
            # Never execute failed_generation or relax the tool allowlist.
            recoveries = 1
            names = [t['function']['name'] for t in tools]
            messages[0]['content'] += ('\nThe preceding generation was rejected for invalid tool use. '
                'Choose only a tool from this turn: ' + ', '.join(names) +
                '. Follow its parameter schema exactly. Tools mentioned in evidence or earlier instructions '
                'are unavailable unless in this list.')
            raw, retries = self.send(request)
        choices = raw.get('choices') or []
        choice = choices[0] if choices else {}
        output = []
        for call in (choice.get('message') or {}).get('tool_calls') or []:
            function = call.get('function') or {}
            if (not isinstance(call.get('id'), str) or not call['id'] or
                    not isinstance(function.get('name'), str) or not function['name'] or
                    not isinstance(function.get('arguments'), str)):
                raise RuntimeError('Groq returned an invalid function call')
            output.append({'type': 'function_call', 'call_id': call['id'],
                           'name': function['name'], 'arguments': function['arguments']})
        usage = raw.get('usage') or {}
        normalized = {target: usage[source] for target, source in {
            'input_tokens': 'prompt_tokens', 'output_tokens': 'completion_tokens', 'total_tokens': 'total_tokens'
        }.items() if source in usage}
        return {'id': raw.get('id'), 'model': raw.get('model'),
                'status': 'completed' if choice.get('finish_reason') == 'tool_calls' and output else 'incomplete',
                'output': output, 'usage': normalized, 'provider': 'groq',
                'provider_response': raw, 'rate_limit_retries': retries,
                'tool_validation_recoveries': recoveries}


def create_model_api(model):
    if model_provider(model) == 'groq':
        return GroqAPI()
    if model_provider(model) == 'gemini':
        return GeminiAPI()
    return API('https://api.openai.com', 'Bearer ' + required('OPENAI_API_KEY'))
