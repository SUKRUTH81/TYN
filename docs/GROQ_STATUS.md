# Groq integration

The local `.env` selects `MODEL_PROVIDER=groq` and `GROQ_MODEL=openai/gpt-oss-120b`. Existing Jira and Gemini credentials were preserved. No credentials are included in this document or the source archive.

The live native function-call doctor passed against Groq: requested `groq/openai/gpt-oss-120b`, actual `openai/gpt-oss-120b`, 145 input tokens, 97 output tokens, 242 total tokens. An explicit application User-Agent resolved the HTTP 403 observed with the initial Python default User-Agent.

The first live Jira assessment is preserved at `artifacts/groq-run-01`. It is PARTIAL, not a finished assessment: four model responses, four tool calls, five Jira HTTP requests and 6,824 reported tokens preceded an explicit HTTP 429 tokens-per-minute rejection. The provider reported a limit of 8,000 TPM, 6,114 used, 2,205 requested and Retry-After 3 seconds. These execution errors are not product evidence.

The adapter now retries explicit HTTP 429 rejection at most twice, only when the provider specifies Retry-After within 0..60 seconds. It does not retry timeouts or 5xx responses. This retry change has local regression coverage but a completed live assessment has not yet been established. Larger individual prompts can still exceed the account's token limit; retries do not increase quota.

Use a new output directory for each real run, then audit it:

```powershell
.\venv\Scripts\python.exe -m release_agent doctor --model-only
.\venv\Scripts\python.exe -m release_agent assess --output artifacts\groq-run-02
.\venv\Scripts\python.exe -m release_agent audit artifacts\groq-run-02 --reference tests\expected_decisions.json
```

No Jira reimport is necessary. Consult https://console.groq.com/settings/limits for the current account limits. No account tier or billing settings were changed.

## Tool validation recovery

`groq-run-02` failed during discovery when the model attempted `get_linked_issues`, which was not offered in that phase. Discovery now has dedicated instructions and each turn explicitly lists its current tools. Execution checks the current turn's allowlist, including the terminal-only final turn.

Groq HTTP 400 `tool_use_failed` permits one corrective generation using the same tools and schemas. Provider tool validation remains enabled, rejected generated calls are never executed, and other HTTP 400 errors are not retried. Successful recovery is recorded as `tool_validation_recoveries` in the response trace and metrics; usage is marked incomplete because the rejected generation's token usage is unavailable. Repeated invalid generations still stop the session.

Live regression check: `artifacts/groq-tool-fix-check` passed discovery and made 10 successful model calls and 9 tool calls without the reported HTTP 400. It was intentionally run with `--max-seconds 120` and ended PARTIAL from global budget exhaustion after the in-flight call completed (135.438 seconds). This establishes successful discovery on that run, not completed assessment correctness. All 51 local tests passed.
