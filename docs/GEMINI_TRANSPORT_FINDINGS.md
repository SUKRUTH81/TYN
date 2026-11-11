# Gemini transport findings

The latest raw, secret-redacted results are in `artifacts/gemini-basic-diagnostic.json`.

The same configured key and model returned HTTP 200 for model metadata (0.296 seconds) and token counting (0.235 seconds). A minimal plain-text generation request timed out through both Python and curl, independently of Jira and agent tools.

Curl observed DNS completion at 0.153 seconds, TCP connection at 0.381 seconds, and TLS completion at 0.433 seconds. TLS verification returned zero (success). The client uploaded the complete 145-byte request. No HTTP status or response bytes arrived before the 15-second timeout (curl exit 28).

The last confirmed stage is therefore **TLS complete, request uploaded, waiting for the first generation response byte**. Client upload does not prove Google received or processed the request. These observations cannot distinguish an intermediary delay from Google's inference processing. They do not establish billing restrictions, exhausted quota, or a particular account problem. Earlier 120-second application timeouts establish that simply restoring that timeout has not solved the issue.

To identify the responsible component, compare this same minimal request on another approved network with identical key/model settings, or correlate the timestamp with provider request logs/support. Do not bypass organizational network controls. Keep credentials out of diagnostic output.

Reproduce with:

```powershell
.\venv\Scripts\python.exe tools\diagnose_gemini_connection.py --basic --timeout 15
```

No credentials, model selection, or proxy settings were changed. All 45 local tests passed after the transport diagnostic change.
