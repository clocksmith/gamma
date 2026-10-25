# Matched 32-problem representation/initialization pilot

This specification precedes fitting and does not contain a result. The fixed 32
IDs and exact reference hashes are frozen by FREEZE.md and the input manifest.
Only independently replayed complete transformation reports may enter this fit.
All 32 IDs remain in every arm, including explicit unsafe-source reference
fallbacks. All source eligibility derives from retained isolated execution
observations, not AST success flags. Reference qualification is independently
replayed from the original400 plus mandatory successor evidence.

Exactly 12 arms: reference/format/role × inherited/fresh × 128/256. The objective
is lexicographic (total selections, total character selections); character-bit
fraction and all M1 thresholds are reported, not optimized post hoc. No dev-val
or protected sources inform proposals, initialization, source choice or fitting.
This fit measures only the 32 fixed fit problems, not the full M1 population.

Each representation gets its own balanced 2–4, 5–8, 9–16, 17–32 and 33–64 byte
proposal buckets (up to 300 entries each), requiring two distinct problem owners.
The same pool is used by both initialization arms. Whole-source/function-body/
Solution-method literals from all three pilot representations are forbidden.

Inherited initialization uses the unchanged pinned 128/256 L-R dictionaries,
canonicalizing only the order of learned entries. Fresh initialization starts
with the exact same 96-character alphabet. Repeatedly select the adjacent pair
with greatest occurrence count, then shorter merged byte length, then lexical
pair order; require two distinct problem owners, merged length <=64, not already
in the dictionary and not a forbidden whole solution/body. Merge non-overlapping
occurrences left-to-right. Store each learned entry as its complete literal text,
not references to earlier tokens. Keep every learned entry, including unused
ones, fully charged. Stop at capacity or no eligible pair. At most32/160 accepted
merges; 10 CPU seconds per seed, failure rather than partial acceptance on expiry.

Both initializations then receive the identical joint-composable single/pair
exchange algorithm: 4 rounds, at most512 exact candidate evaluations, 60 CPU
seconds per arm, 4 additions per length bucket, 8 single-removal candidates,
4 pair-removal candidates and12 complementary-pair proposals. Every problem has
one fixed source, so source selection cannot favor an arm after measurements.
CPU limits are resource ceilings chosen before any pilot fitting, not tuning
based on results. Failure retains its evidence; no smaller machine-dependent
partial dictionary is accepted as a completed arm.

Seal all 12 dictionaries before publishing any per-arm measurement. Report seed
and optimized measurements separately, with exact source bytes, learned literals,
framing, padding, packets and the existing complete independent decoder cost.
All helpers and existing solve adapters remain fully present in source bytes;
there are no hidden macros or uncharged helpers. Two independent segmenters and
an independent packet decoder must exactly reconstruct every source. Recheck code
and qualified source hashes at the end. Retain private strings/traces/packets
outside the repository; only aggregate results and hashes may be public.
