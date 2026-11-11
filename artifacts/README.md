# Historical execution artifacts

This directory preserves the available diagnostic outputs and previous execution attempts for transparency. These files are historical evidence; they are not a successful final release assessment.

## Recorded outcomes

| Directory / file | Recorded state | Interpretation |
|---|---|---|
| `import-audit.json` | Verified | Records 400 issues, 2,059 comments and 76 links for the supplied dataset. |
| `groq-run-01/` | `PARTIAL`, `live_jira` | Real Jira-backed attempt; incomplete assessment. |
| `groq-run-02/` | `FAILED`, `live_jira` | Tool-call validation error: model attempted to call a tool not included in the request. |
| `groq-run-03/` | `PARTIAL`, `live_jira` | Real Jira-backed attempt; incomplete assessment. |
| `groq-tool-fix-check/` | `PARTIAL`, `live_jira` | Follow-up tool-validation check; incomplete assessment. |
| `live-final/`, `live-run-01/` | `FAILED`, `live_jira` | Gemini attempts stopped before Jira evidence gathering after HTTP 429 responses. |
| `live-model-validation-*` | `FAILED` or `PARTIAL`, `live_gemini_offline_jira` | Model plumbing tests against an offline Jira double; not live-Jira assessment evidence. |
| `offline-pipeline*/` | `COMPLETED`, `offline_test_double` | Scripted offline fixture pipeline. This is not a live model or live Jira assessment. |
| `quality-run-01/` | `FAILED`, `live_jira` | Model request timed out before Jira evidence gathering. |
| `gemini-*-diagnostic*` and `*-tests.txt` | Diagnostic outputs | Historical provider/transport troubleshooting. |

## Submission status

No completed live Jira assessment is present in this directory. In particular, the completed offline pipeline must not be described as the requested live assessment. The required final evidence is a fresh run with `provenance=live_jira`, `assessment_complete=true`, and metrics `status=COMPLETED`, followed by a successful independent audit. Store that run in a clearly named directory such as `artifacts/live-run/` only after it meets those conditions.

The local `.env` file and API credentials are intentionally excluded from this source package. Copy `.env.example` to `.env` locally and populate it on your own machine; never commit or email `.env`.
