# Identifying Gemini timeouts

A timeout means the client did not receive a complete HTTP response. It is not an HTTP 429/503 and does not by itself prove a quota, billing or provider outage cause.

## Step 1: metadata only

```powershell
.\venv\Scripts\python.exe tools\diagnose_gemini_connection.py --metadata-only --timeout 20
```

This makes no generation request and writes `artifacts/gemini-metadata-diagnostic.json`. HTTP 200 proves that metadata is accessible with this key, not that generation is enabled or billing/quota is usable. See [Google's troubleshooting guide](https://aistudio.google.com/docs/troubleshooting).

## Step 2: one bounded generation comparison

```powershell
.\venv\Scripts\python.exe tools\diagnose_gemini_connection.py --timeout 20
```

This makes a small Interactions function-call probe and, only for a timeout/5xx, a GenerateContent function-call probe. It can use API credits. No retries, model changes, credential changes or proxy bypasses occur. Sanitized responses are saved to `artifacts/gemini-connection-diagnostic.json`.

| Observation | Supported conclusion |
| --- | --- |
| 400 | Inspect model/endpoint/request-format error |
| 401 / 403 | Inspect the explicit key/permissions/project/billing error |
| 429 | Inspect quota metric and Retry-After to identify RPM, TPM or daily limits |
| 503 | Provider returned service unavailable; inspect message and Retry-After |
| Interactions fails, GenerateContent succeeds | Investigate the Interactions endpoint/request path |
| Both time out, metadata succeeds | Generation-specific delay; exact location/cause remains unproven |
| Metadata also has connection/DNS/TLS errors | Investigate the local network/proxy/certificate path |

Proxy variable names are reported without values. An environment variable's presence is not evidence that the proxy caused a failure. Do not disable TLS verification or organizational network controls.

## Step 3: project-side evidence

In [AI Studio](https://aistudio.google.com/apikey), locate the current key's owning project. Check that project's eligibility, billing state and [rate limits](https://aistudio.google.com/rate-limit). Metadata-only endpoints do not perform all inference eligibility checks.

Compare a controlled API test from another approved client using the same project and model. A successful AI Studio chat alone does not establish that the exact API key/project inference route works. Use Cloud request/error metrics or provider support to investigate repeated timeouts when no HTTP error body is returned.

Resume the assessment only after a native function-calling doctor check succeeds. Use a fresh artifact directory; do not repeat the Jira import to address a Gemini timeout.

## Isolate basic inference from function calling

```powershell
.\venv\Scripts\python.exe tools\diagnose_gemini_connection.py --basic --timeout 20
```

This compares metadata, a non-generating token-count POST, and one plain-text generation request. If the Python token-count request times out, the diagnostic also compares that non-generating request using curl when installed. The key is passed through stdin, not command arguments. Proxy settings are retained. A successful token count does not prove generation access or adequate quota. The basic check makes one generation request and saves `artifacts/gemini-basic-diagnostic.json`.
