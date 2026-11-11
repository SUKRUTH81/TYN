# Submission checklist

1. Keep a dedicated Jira Cloud project and configure local `.env`.
2. Run `python -m release_agent doctor`, import, and `verify-import`.
3. Run the actual Gemini assessment against live Jira into a fresh artifact directory.
4. Check `assessment_complete=true`, `provenance=live_jira`, no ERROR requirement statuses, and metrics `COMPLETED`.
5. Review each requirement's rationale, scope, actor/role, chronology, rejected evidence and outstanding action. Open its actual Jira issue/comment links.
6. Run the generic artifact audit. Optionally run the independent fixture audit after generation. Investigate discrepancies rather than modifying decisions to fit a key.
7. Package with `tools/package_submission.py --run DIRECTORY`. The packager rejects partial runs and both offline provenance modes.
8. Inspect the zip for source, brief/dataset, tests, documentation, actual report, trace and measured usage. `.env`, API tokens, development secret, database, node_modules and caches must be absent.
9. Share the zip or repository as the assessment email requests. Confirm access if using a private repository. Do not send credentials.

The expected fixture outcomes are development-only; they are not a replacement for a generated live Jira report. Local/source-only packages are useful for review but do not meet the actual-report requirement until the live run is completed.
