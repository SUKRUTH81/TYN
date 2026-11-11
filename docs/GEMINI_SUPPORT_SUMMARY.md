# Gemini inference timeout: support summary

No credentials or project settings were changed.

Configured model: gemini-3.8-flash
Checked at UTC: 2026-11-11T13:00:09.897511+00:00

| Operation | HTTP status | Elapsed seconds |
|---|---|---|
| model_metadata | 200 | 0.312 |
| count_tokens | 200 | 0.25 |
| plain_text_generation | No complete response | 20.109 |

A plain-text inference request without tools also timed out. The Jira importer, Jira tools and final report generation were not involved in that probe.

Project ID and inference eligibility: not yet verified. Please check the current key?s owning project and any verification, billing, quota or restriction status in AI Studio.

For provider/network support: investigate why metadata and token counting respond while inference does not return a complete HTTP response. Diagnostic timeout alone does not identify which layer caused the delay.

Sanitized details: artifacts/gemini-basic-diagnostic.json and artifacts/gemini-connection-diagnostic.json. Do not attach .env or API keys.
