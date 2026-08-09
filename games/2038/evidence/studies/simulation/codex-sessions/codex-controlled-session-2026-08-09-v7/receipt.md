# Codex controlled-session failed-attempt receipt

Session: `codex-controlled-session-2026-08-09-v7`

Evidence: **failed LLM simulation diagnostic**, not a human playtest

The run wrote its live journal outside the repository. It completed four
unboxing records, forty-four lossless source-chunk readings, four rules
syntheses, and all eleven initial facilitator evidence passes. One provider
attempt timed out during Card Reference part 3 and its identical retry
succeeded.

Initial answer synthesis then returned the citation `core-rules#Era cards`.
`Era cards` is a real heading in Card Reference, not Core Rules. The semantic
validator rejected the mismatched source-heading pair, and the run failed
closed before participant follow-up, final readiness, gameplay, or postgame
reconstruction.

The response schema had independently enumerated every valid source ID and
every valid heading, which permitted invalid cross-source combinations. The
locked successor `codex-controlled-session-2026-08-09-v8` constrains each
source ID to headings from that source while retaining the same release, kit,
seed, participants, provider policy, and external-output requirement.
