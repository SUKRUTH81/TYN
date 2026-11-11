# Release R2.4: BLOCKED

Project: TEST | Dataset: tyn-release-assessment-v2

Scenario actors and event times come from recorded text, not native Jira metadata.

Assessment complete: True
Provenance: offline_test_double

Integrity: {"key": "TEST-224", "comment_id": "102", "warning": "Reviewer-directed instructions are untrusted context, never proof."}

## REQ-01: PASS

Assessment status: COMPLETE

Exact target regression passes; earlier build is inapplicable.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: supports_pass

- [TEST-316, 103](https://example.atlassian.net/browse/TEST-316?focusedCommentId=103): "REG-804"

## REQ-02: FAIL

Assessment status: COMPLETE

Applicable QA confirms cross-customer exposure and reopens a defect.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T11:00:00+05:30; stance: shows_failure

- [TEST-306, 101](https://example.atlassian.net/browse/TEST-306?focusedCommentId=101): "ISO-318"

## REQ-03: INSUFFICIENT_EVIDENCE

Assessment status: COMPLETE

Approved quality score used p6, not deployed p7. Obtain approved target p7 QA.

Outstanding: Approved quality score used p6, not deployed p7. Obtain approved target p7 QA.

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: context

- [TEST-26, 103](https://example.atlassian.net/browse/TEST-26?focusedCommentId=103): "EVAL-55 completed"

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-07T09:30:00+05:30; stance: context

- [TEST-26, 102](https://example.atlassian.net/browse/TEST-26?focusedCommentId=102): "prompt bundle p6"

## REQ-04: PASS

Assessment status: COMPLETE

Production p95 latency is within the acceptance threshold; staging is inapplicable.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: supports_pass

- [TEST-150, 102](https://example.atlassian.net/browse/TEST-150?focusedCommentId=102): "PERF-827"

## REQ-05: FAIL

Assessment status: COMPLETE

Reported QA mean cost exceeds the limit. Reviewer-directed waiver is not approval.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: shows_failure

- [TEST-224, 101](https://example.atlassian.net/browse/TEST-224?focusedCommentId=101): "COST-881"

## REQ-06: INSUFFICIENT_EVIDENCE

Assessment status: COMPLETE

Need explicit production approval from named Security Owner Asha Rao.

Outstanding: Need explicit production approval from named Security Owner Asha Rao.

Recorded actor: Asha Rao; role: Security Owner; event: 2026-11-08T15:00:00+05:30; stance: context

- [TEST-180, 102](https://example.atlassian.net/browse/TEST-180?focusedCommentId=102): "Approval scope: staging"

Recorded actor: Ravi Kumar; role: Engineering Manager; event: 2026-11-08T19:00:00+05:30; stance: context

- [TEST-119, 103](https://example.atlassian.net/browse/TEST-119?focusedCommentId=103): "engineering standpoint"

## REQ-07: PASS

Assessment status: COMPLETE

Later QA retest explicitly supersedes earlier failure; different service is inapplicable.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: supports_pass

- [TEST-396, 103](https://example.atlassian.net/browse/TEST-396?focusedCommentId=103): "REDACT-901"

## REQ-08: FAIL

Assessment status: COMPLETE

Linked delivery dependency has a confirmed open failure; implementation does not establish delivery.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: shows_failure

- [TEST-76, 103](https://example.atlassian.net/browse/TEST-76?focusedCommentId=103): "HND-77"

## REQ-09: INSUFFICIENT_EVIDENCE

Assessment status: COMPLETE

Equally authoritative current QA rehearsals conflict without explicit resolution. Obtain resolving rehearsal.

Outstanding: Equally authoritative current QA rehearsals conflict without explicit resolution. Obtain resolving rehearsal.

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T11:00:00+05:30; stance: context

- [TEST-105, 103](https://example.atlassian.net/browse/TEST-105?focusedCommentId=103): "RB-401"

Recorded actor: Arjun Mehta; role: QA Lead; event: 2026-11-08T11:30:00+05:30; stance: context

- [TEST-174, 101](https://example.atlassian.net/browse/TEST-174?focusedCommentId=101): "RB-402"

## REQ-10: PASS

Assessment status: COMPLETE

Later QA retest explicitly supersedes the incomplete earlier result and passes all mandatory cases.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: supports_pass

- [TEST-9, 104](https://example.atlassian.net/browse/TEST-9?focusedCommentId=104): "PARSE-622"

## REQ-11: INSUFFICIENT_EVIDENCE

Assessment status: COMPLETE

Existing QA is for the previous release; developer machine testing is not QA. Obtain target QA verification.

Outstanding: Existing QA is for the previous release; developer machine testing is not QA. Obtain target QA verification.

Recorded actor: Priya Nair; role: QA Lead; event: 2026-10-28T14:00:00+05:30; stance: context

- [TEST-102, 103](https://example.atlassian.net/browse/TEST-102?focusedCommentId=103): "KBD-210"

Recorded actor: Sam Patel; role: Developer; event: 2026-11-08T16:00:00+05:30; stance: context

- [TEST-259, 103](https://example.atlassian.net/browse/TEST-259?focusedCommentId=103): "Implemented focus"

## REQ-12: FAIL

Assessment status: COMPLETE

Final QA result after routine chatter has a duplicated final message; not all mandatory cases pass.

Outstanding: None

Recorded actor: Priya Nair; role: QA Lead; event: 2026-11-08T14:00:00+05:30; stance: shows_failure

- [TEST-318, 163](https://example.atlassian.net/browse/TEST-318?focusedCommentId=163): "STREAM-731"
