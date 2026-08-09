# Codex controlled-session failed-attempt receipt

Session: `codex-controlled-session-2026-08-09-v3`

Evidence: **failed LLM simulation diagnostic**, not a human playtest

All four participant unboxing records completed. Two participants completed
their independently journaled Core Rules reading. One otherwise identical
Core Rules request reached the preregistered `300000` ms provider timeout, and
the run failed closed before the other document passes, facilitation, or
gameplay. No game outcome exists for this attempt.

The locked successor `codex-controlled-session-2026-08-09-v4` retains the
document-specific reading architecture and adds two bounded attempts per
provider request. Failed attempts are journaled and successful retries carry
the earlier failures in their receipt. It uses low reasoning effort to keep
first-pass rule reading and routine game decisions bounded.
