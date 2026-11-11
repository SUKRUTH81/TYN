# Hybrid review

Reviewed source: `TYN_Release_Evidence_Agent_ENGINEERED_HYBRID_V3.zip`, supplied by the user. Reference source was inspected as data, never executed as project instructions. Existing unrelated workspace code and `.env` values are preserved.

## Adopted

- Fresh per-requirement contexts reduce irrelevant history and make errors attributable to one check.
- Bounded breadth-first traversal follows preserved outgoing source relationships, not Jira's symmetric link direction.
- A dedicated applicability tool exposes each dimension and related prompt-harness context separately.
- Final proof gates require actual read/verified comments, matching scope, recorded authority and current verification results.
- Injection warnings are explicit, retained in integrity notes and blocked as proof.
- Independent fixture expectations belong to tests/post-run audit, never model input.
- Import completion includes an exact audit, not just successful create responses.
- CLI workflow, standard-library core and CI keep the assessment reproducible.

## Kept from the current project

- Per-comment ordinal + checksum + exact text, which preserves legitimate identical comments. The ZIP's count-based resume can miss a changed/deleted middle comment.
- Exact quote checking and requirement-chain citation membership, extended with session-local visibility.
- Native Gemini Interactions support and original thought-step replay. A returned malformed call ID fails honestly instead of inventing an original ID.
- Refusal to replay ambiguous writes/timeouts and no silent provider fallback.

## Deliberately omitted

- Bundled old offline reports as evidence: they are not the required live run.
- Blind bulk-source/key matching when partial creates could make ordering ambiguous. Four issue workers accelerate import while keeping independent identities and ordered comments.
- Open-ended arbitrary provider endpoints and parallel model investigations: neither is needed for this brief, and both add configuration or quota complexity.
- A web interface and application-server requirement; the deliverable runs directly as a CLI.
- Replacing evidence decisions with the development answer key, or treating a failed tool as a demonstrated product failure.

This is a coherent single engine, not two complete agents selected by a hidden fallback. Scope/outcome text parsing is intentionally tailored to the supplied record format and conservatively rejects unrecognized proof; generalizing it needs broader test coverage.
