# Codex controlled-session failed-attempt receipt

Session: `codex-controlled-session-2026-08-09-v1`

Evidence: **failed LLM simulation diagnostic**, not a human playtest

The four participant unboxing records completed and remain in
`stage-journal.jsonl`. During complete Default Game rules reading, one Codex
process reached the preregistered `120000` ms provider timeout. The run failed
closed before facilitation or gameplay. No game decision or outcome exists for
this attempt.

The locked successor `codex-controlled-session-2026-08-09-v2` changes only
the provider timeout guard and partial-participant journaling. It preserves the
same release, ruleset fingerprint, seed, factions, profiles, model, reasoning
effort, and evidence boundary.
