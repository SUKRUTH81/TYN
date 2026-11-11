# Release R2.4: NEEDS_REVIEW

Project: TYN | Dataset: tyn-release-assessment-v2

Scenario actors and event times come from recorded text, not native Jira metadata.

Assessment complete: False
Provenance: live_jira

Integrity: {"warning": "Some investigations failed. Overall decision is conditional; never treat this as a completed assessment."}

## REQ-01: PASS

Assessment status: COMPLETE

The requirement REQ-01 demands that all automated regression cases pass on the target build (R2.4, commit b7a91f2, service atlas-assistant, production). Evidence REC-2081 (issue TYN-316) records a regression run REG-804 that matches the exact release, commit, service, and environment, reporting 146 of 146 mandatory cases passed, which satisfies the acceptance criterion. The earlier regression run REC-2299 (issue TYN-130) pertains to a different commit and does not affect this target. No security approvals or defect blocks are relevant for this requirement.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: supports_pass

- [TYN-316, 11580](https://tyn-ai-assessment.atlassian.net/browse/TYN-316?focusedCommentId=11580): "Completed regression run REG-804: release R2.4; commit b7a91f2; service atlas-assistant; environment production. 146 of 146 mandatory regression cases pass."

## REQ-02: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: APIError: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-03: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-04: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-05: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-06: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-07: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-08: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-09: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-10: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-11: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.

## REQ-12: INSUFFICIENT_EVIDENCE

Assessment status: ERROR

Investigation incomplete because tooling/model execution failed: RuntimeError: Provider authentication/quota failure; remaining investigations were not sent: API request failed: HTTP 429; POST /openai/v1/chat/completions; Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01ky1wn7n0exgaw02f2nfpmv6z` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 2914, Requested 5148. Please try again in 464.999999ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing

Outstanding: Rerun this investigation or perform a manual Jira review; this is not a finding of missing product evidence.
