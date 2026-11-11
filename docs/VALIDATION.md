# Validation results

- 53 CLI/import/evidence/provider/audit/diagnostic tests pass, including redacted provider-error messages and timeout-stage reporting.
- Core input validation also runs with Python `-S` (site packages disabled).
- The complete offline fixture pipeline passes the independent twelve-requirement decision audit.
- Real Jira import audit passed for 400 issues, 2,059 comments and 76 links.
- An earlier Gemini function-calling probe passed. After the key was updated, model metadata returns 200, while recent generation probes time out; earlier probes returned 503 high demand; see RUN_STATUS.md.

Tests cover wrong builds, services, environments and prompts; named security approval; explicit supersession; unresolved QA conflicts; dependency failures; last-comment streaming evidence; injection warnings; quote/read/scope gates; partial failure isolation; comment checksums and intentional duplicates; ordered parallel imports; resumability; usage metadata; native Gemini thought/call replay; bounded 429 retry; no retry for ambiguous server errors; artifact audit; CLI exits.

Passing protocol/scripted tests does not establish real model decision accuracy. There is no completed live model assessment yet, and no offline sample is represented as one.
