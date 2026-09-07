# Three Headline simplification

Implemented in executable 0.19.10, physical rules candidate 0.11.0-rc.12-test.

- Analog Havens pays 2 Runway for 2 Trust and removal of 2 Scrutiny; Customers and their awards remain unchanged.
- Limb Liquidity permits ordinary reassignment of one Agent, including staying put, without payment, rival consent, or extra bonuses.
- Wartime Water Bridge automatically awards 1 Trust and removes 1 Scrutiny once per institution with a connected Facility adjacent to a connected rival Facility. Co-location, offline hosts, and own-only adjacency do not qualify.

The component records, executable, lore newswires, and generated references agree. All 24 Headlines remain, six per Era with three revealed. Seven original vignette sections were compared byte for byte against 1136ee4d and are unchanged. Rules procedures, physical state encoding, and browser renderer need no separate change: these effects reuse payment, assignment, and existing connectivity.

## Verification

304 tests pass, with no failures or skips. Build, content/project checks, release verification, and whitespace checks pass. Focused regressions cover affordability, caps, permanent Customer awards, ordinary assignment without bonuses, adjacency exclusions, once-only rewards, and the runtime decision contract at 2–5 players. This is automated functional evidence, not a browser visual check, human learning study, or balance result. The two-Runway price remains provisional.

## Retained failures

The initial build rejected the new scenario revision until its explicit three-scenario authorization was added. The first full suite passed 302 tests and failed two content contracts: Limb Liquidity needed numeric card typography and a third descriptive tag. Both were corrected; the final suite passes. Initial logs and the earlier 0.19.9 / rc.11 release evidence remain preserved. verification.json hashes the changed source files and logs.

Fusion, Joint Venture limits, Era Mandates, AGI timing, and shared breakthrough mechanics are outside this pass. Human playtesting remains outstanding. No push or deployment was performed.
