# Execution status

## Source and test validation

- The source package was validated with `python -m unittest discover -s tests -v`: **53 tests passed**.
- The test suite includes scripted/offline pipeline, evidence validation, tool-call handling, provider error handling, audit behavior, and report rendering tests.
- These tests do not establish that a live model completed the assigned Jira assessment.

## Jira import evidence

The preserved `artifacts/import-audit.json` records a verified import with:

- 400 issues
- 2,059 comments
- 76 links
- Input SHA-256: `78ff61d1402a4f815746c3b31116bff0d6932242286af34bddec951b4e0d308a`

This is the recorded import-audit result. Run `verify-import` against the currently configured Jira project again before relying on the import for a final assessment.

## Historical model and assessment attempts

The `artifacts/` directory retains prior outputs and diagnostics:

- Groq run 01: `PARTIAL`, provenance `live_jira`.
- Groq run 02: `FAILED`, provenance `live_jira`, due to a tool-call validation error.
- Groq run 03: `PARTIAL`, provenance `live_jira`.
- Groq tool-fix check: `PARTIAL`, provenance `live_jira`.
- Gemini `live-final` and `live-run-01`: `FAILED`, provenance `live_jira`, with HTTP 429 responses before Jira evidence gathering.
- Gemini model-validation attempts: `FAILED` or `PARTIAL`, provenance `live_gemini_offline_jira`; these used an offline Jira double.
- Offline pipeline runs: `COMPLETED`, provenance `offline_test_double`; these are scripted tests, not live assessments.
- `quality-run-01`: `FAILED` after a model request timeout before Jira evidence gathering.

The individual `metrics.json`, `report.json`, and trace files contain the details for each run. Failed and partial attempts are preserved rather than relabeled as successful.

## Final assessment status

**No completed live Jira assessment report is currently available.** Do not represent any historical or offline run as satisfying the final-report requirement. The required final run must have:

- `provenance=live_jira`
- `assessment_complete=true`
- metrics `status=COMPLETED`
- no unresolved execution errors in requirement assessments
- a successful independent audit

Generate the final report, trace, and metrics in a fresh output directory only after the live model and Jira checks succeed. Then run the audit and package with `tools/package_submission.py --run DIRECTORY`.

## Credential handling

The original working archive contained a populated `.env`. It has been removed from this package. `.env.example` contains placeholders only. Add real credentials locally after extraction; never commit or send `.env`, tokens, API keys, or credential-bearing logs.
