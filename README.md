# TYN Release Evidence Agent - engineered hybrid

A tool-using agent that investigates software-release requirements using scoped Jira evidence. This is a **Python CLI with no third-party runtime dependencies**. Groq and Gemini have separate provider adapters.

### Groq configuration

Set these values in your local `.env` (never commit the real key):

```dotenv
MODEL_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=your_key_here
MODEL_TIMEOUT_SECONDS=120
```

Create your key at https://console.groq.com/keys. Groq's production model list is at https://console.groq.com/docs/models.
The adapter uses `POST https://api.groq.com/openai/v1/chat/completions`, with required local tool calling, matching call IDs and normalized token usage. No SDK dependency is needed. Explicit Groq HTTP 429 rejections allow at most two retries when Retry-After is present and no more than 60 seconds. Other errors and timeouts are not replayed; there is no provider fallback. Account rate and token limits still apply.

```powershell
.\venv\Scripts\python.exe -m release_agent doctor --model-only
.\venv\Scripts\python.exe -m release_agent assess --output artifacts\groq-run-01
.\venv\Scripts\python.exe -m release_agent audit artifacts\groq-run-01 --reference tests\expected_decisions.json
```

The first command must verify a real tool call before assessment. Jira does not need reimporting when changing model providers. An explicit CLI model override uses `--model groq/openai/gpt-oss-120b`; the leading `groq/` selects the adapter and is removed before transmission. Set `MODEL_PROVIDER=gemini` to use the existing Gemini configuration instead. Gemini-specific diagnostic scripts continue to test Gemini regardless of the selected assessment provider.

The assessment brief evaluates evidence correctness, applicability, tool use, context management and reproducibility. The CLI exposes those behaviors through repeatable commands.

## Quick start

Use Python 3.11 or later. From the project root:

```powershell
# On a fresh checkout:
py -3.11 -m venv venv

.\venv\Scripts\python.exe -m release_agent validate-input
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

There are no packages to install for the CLI. Linux/macOS use `venv/bin/python` or `python3` instead of the Windows executable.

Fill in `.env` locally (copy `.env.example` on a fresh checkout):

```dotenv
JIRA_BASE_URL=https://YOUR-SITE.atlassian.net
JIRA_EMAIL=your-atlassian-account-email
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=TYN
MODEL_PROVIDER=groq
GROQ_API_KEY=your-groq-key
GROQ_MODEL=openai/gpt-oss-120b
MODEL_TIMEOUT_SECONDS=120
```

Use a dedicated Jira Cloud project with `Task` issues and `Relates` links enabled. The account needs issue/comment/link creation and browse access. Keep credentials out of Git, zips, chat and reports. Environment variables override `.env`; restart long-running web/worker processes after changes.

## Run the real assessment

Each assessment writes both `report.md` and a standalone `report.html`. Open the HTML file in a browser for decision counts, target scope, requirement cards, expandable cited evidence and execution metrics. It works offline without a frontend server or external assets; Jira links require Jira access. Browser Print → Save as PDF exports the visual report. Incomplete runs clearly separate execution errors from evidence decisions.

To create the HTML view for an existing run without making API requests:

```powershell
.\venv\Scripts\python.exe tools\render_report.py artifacts\groq-run-03
Start-Process artifacts\groq-run-03\report.html
```

```powershell
# Small real connectivity/tool-calling probe; incurs a small model request.
.\venv\Scripts\python.exe -m release_agent doctor

# Repeatable import; four independent issues at a time, ordered comments within each.
.\venv\Scripts\python.exe -m release_agent import --workers 4

# Verifies source IDs, exact descriptions, exact marked comments, duplicates and links.
.\venv\Scripts\python.exe -m release_agent verify-import --workers 4

# Agent gathers evidence from live Jira. No dataset/import-map argument exists here.
.\venv\Scripts\python.exe -m release_agent assess --release R2.4 --output artifacts/live-run

# Fail-closed artifact/coverage/trace audit.
.\venv\Scripts\python.exe -m release_agent audit artifacts/live-run
```


All Jira operations accept `--project` and `--scope`. The dataset scope for this brief must be `tyn-release-assessment-v2`. Import/verification accept `--dataset` and `--workers 1..8`; issue/link type names can be overridden on import. `doctor --jira-only` and `doctor --model-only` isolate configuration problems.

## What was combined

| Capability | Chosen implementation |
| --- | --- |
| Evidence and provenance | Current project: exact source identity, lossless ADF, per-comment ordinal/checksum, quotes validated against fetched text |
| Context management | ZIP concept, reimplemented in the current engine: model discovery followed by a fresh conversation per requirement |
| Traversal | Source-directed bounded BFS; generic Jira Relates backlinks do not expand into sibling requirements |
| Applicability | Explicit scope-check tool and final code checks for release, exact commit, service, production and required prompt |
| Authority and chronology | Recorded actors/roles/times, named Security Owner checks, explicit later supersession and unresolved QA conflict gates |
| Injection handling | Source text remains visible as data; reviewer-directed instructions are flagged and cannot establish PASS/FAIL |
| Reproducibility | Exact import audit, independent post-run audit, scripted fixture tests, CLI workflow and CI |
| Model integration | Groq chat tool calling or native Gemini Interactions; call-ID matching, usage metadata and no silent fallback |

See [the comparison](docs/HYBRID_REVIEW.md) and [design/limits](docs/DESIGN.md). The supplied ZIP's example reports and answer key are not live evidence and are never fed to the model.

## How the agent works

1. The model calls tools to discover and read the scoped release manifest, then declares its exact requirement set. Code rejects omissions, additions and duplicates.
2. Each requirement gets a fresh bounded conversation. The model reads the requirement, follows outgoing linked evidence/dependencies, and checks specific comments. Shared Jira caching saves requests, but proof must be exposed and checked in the current session.
3. Known routine chatter is grouped with count and comment IDs. All unfamiliar text is returned in full, and every original comment remains retrievable by page. The final streaming QA result is not hidden behind routine notes.
4. The model submits one decision with exact quotes, citation IDs, evidence stances, rationale and outstanding actions. Code verifies coverage, current proof, scope, recorded QA/named authority, explicit supersession, contradictions and dependency closure. Unrecognized proof wording is conservative and may require manual review.
5. Code computes overall readiness: any mandatory FAIL blocks; otherwise any insufficient item requires review; only all mandatory PASS is READY. A tooling failure is separately marked `assessment_status=ERROR` / `decision_basis=TOOLING_FAILURE`, never a product FAIL.

There is no fixed answer script in the live runtime, no whole-dataset model prompt, no external evidence tool and no Jira-writing tool during assessment. The dataset loader is used for import/audit and explicit offline tests only.

## Outputs and audits

Each fresh output directory contains:

- `report.md`: requirement decisions, rationale, outstanding verification, recorded scenario actors/times and clickable Jira issue/comment citations.
- `report.json`: the same data, target, provenance, integrity warnings and completion flag.
- `trace.jsonl`: session-tagged actual model responses and selected tool calls/arguments/results, including rejected submissions.
- `metrics.json`: execution time, calls, requested/returned models, response IDs when available, reported token usage, configured limits and trace digest.

Successful live runs have `provenance=live_jira`, `assessment_complete=true` and metrics status `COMPLETED`. A partial run preserves verified decisions and explicitly marks unfinished investigations; its metrics status is `PARTIAL`, exit code is 2, and packaging rejects it. Fatal discovery/configuration failures exit 1 with failure trace/metrics. A cryptographic digest detects accidental trace edits; it is not an attestation that an untrusted operator could not rewrite artifacts.

The optional development audit compares to independently reviewed fixture expectations **after** generation:

```powershell
.\venv\Scripts\python.exe -m release_agent audit artifacts/live-run --reference tests/expected_decisions.json
```

The live agent never imports those expectations. A mismatch is a review finding, not permission to rewrite a model result until it matches.

## Bounds, quotas and recovery

CLI defaults: 180 total tool calls, 1,800 seconds, 1,000,000 cumulative provider tokens, 12 model turns and 120 seconds per requirement. Override CLI `--max-calls`, `--max-seconds`, `--max-tokens`, `--max-requirement-turns`. The last turn only offers the phase's submission tool.

Gemini requests are paced at `GEMINI_RPM` (8 by default; 0 disables pacing). Match this to your account quota. Explicit HTTP 429 rejections get at most two retries with `Retry-After` when short enough, otherwise bounded backoff. A repeated provider authentication/quota error stops further provider requests and marks remaining items as unfinished. Timeouts and ambiguous network/5xx errors are not automatically replayed. Import writes are not blindly replayed either.

Limits are checked between calls; a request or bounded retry already in flight can overshoot the deadline. Returned usage is summed, and `usage_complete=false` discloses missing provider usage. A failed request may still incur charges. No monetary total is invented from incomplete usage.

Re-run import safely after a partial failure once Jira indexing has settled. Identity comes from scoped Jira labels, not a local checkpoint. Comments use source ID + ordinal + checksum + exact text, preserving intentional duplicates. Descriptions are verified before resuming. Local import maps are convenience artifacts and are not assessment inputs. Do not run overlapping importers against the same project. Read-only import audit checks all records again before reporting success.

## Offline verification

```powershell
.\venv\Scripts\python.exe tools/offline_demo.py
```

This exercises the real importer, tools, gates, reports and audits against an in-memory Jira protocol double and a scripted model. Its provenance is `offline_test_double`, and it cannot be packaged as the required live report. Use a fresh/removed output directory if rerunning because traces are never overwritten.

`tools/validate_live_model.py` optionally tests the actual Gemini model against the offline Jira double and consumes API credits. Its separate `live_gemini_offline_jira` provenance also prevents submission as live Jira evidence. These modes test plumbing/decision behavior but do not replace the actual assessment.

## Package the deliverable

```powershell
# Clean, runnable CLI source without credentials or caches.
.\venv\Scripts\python.exe tools/package_submission.py --source-only

# Actual completed live report + source; audits and provenance must pass.
.\venv\Scripts\python.exe tools/package_submission.py --run artifacts/live-run
```

The source package is `tyn-cli-source.zip`. Read [the submission checklist](docs/SUBMISSION_CHECKLIST.md) and [run status](RUN_STATUS.md). Repository/email submission is a separate user action.

AI assistance: Codex compared the user-supplied ZIP with the existing code, selected/reimplemented the useful features, added tests and ran validation. Development expectations were checked against the supplied fictional records. Actual release judgments are generated by the configured model through Jira tools and independently audited afterward. Known limits and incomplete live checks are disclosed.

## Publish to GitHub in one go (Windows PowerShell)

After extracting this project and opening PowerShell in the `TYN` folder, install Git, Python 3.11+, and GitHub CLI (`gh`). Authenticate once with `gh auth login`, then run:

```powershell
.\publish_to_github.ps1
```

The script verifies the GitHub account is `SUKRUTH81`, runs the test suite, checks that `.env` is absent, stages the existing source and historical `artifacts/`, creates the public `SUKRUTH81/jira-release-evidence-agent` repository, and pushes `main`. It refuses to overwrite an existing repository or push to an unexpected remote. No GitHub token is stored in the project.

Historical artifact statuses are preserved. Partial, failed, and offline test-double runs are not presented as a completed live Jira assessment.
