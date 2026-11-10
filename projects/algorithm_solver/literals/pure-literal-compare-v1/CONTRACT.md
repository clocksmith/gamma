# Pure literal comparison, frozen before source fitting

Owner request on 2026-11-10: "Try pure literals". This is a new matched
representation experiment on the existing 300-fit/100-exposed development
partition, separately for JavaScript and Python. It does not open protected
families or modify recognition, qualification, the semantic runtime or prior
experiments. Only KnownSpecService may supply exact receipt-bound source bytes.

Every code selects one exact stored nonempty string. Concatenation does no work
other than joining those strings. There are no macro parameters, spell controls,
implicit bindings, injected helpers, transformations or source escapes. Ordinary
single-character entries are charged and their absolute bits/fraction reported.
The original LTD1/LTV1 codec binds the dictionary and charges 41 framing bytes
per program, packed width-6/7/8 IDs, padding and dictionary storage. This differs
from the nine-byte macro/fragment framing; comparisons show the difference.

Fit three alphabet-plus-pair-merging candidates with 0/8/16 slots initially
reserved for merges. Compare frequency-only and coverage-first alphabets too.
For a dictionary too small for every fitting character, coverage-first greedy
source-alphabet unions use the empty seed and eight smallest source alphabets,
plus the frequency control. Pair candidates have at least two distinct fitting
source hashes, at most 160 UTF-8 bytes, and contain no complete fitting source,
function/class unit or function body. The original AST extractor supplies bans.
All pair entries are stored flat, including every byte; decoding never expands
merge rules. Repeated pair counts ignore overlap. Retain every selected merge
and every candidate arm score; rejected alternatives are reproducible.

Choose the greatest complete fitting coverage, then the smallest total exact
minimum-selection cost, then dictionary bytes and method name. Exact DAG
segmentation decides every final sequence. This bounded search is not optimal.
Seal all three width tables before opening validation source for that language.
Validation does not choose arms or tune them. Count unavailable/uncovered IDs
in each original denominator; never compare smaller incomplete totals as wins.
Publish only hashes and source-free aggregates/receipts; keep exact dictionaries
and packets private beside the existing private source packages.

Budget: one CPU process, no models/GPU/training/source execution; 400 IDs per
language, five candidates per width, at most 256 entries and 64 KiB per source.
Focused alphabet/merge/codec and source-boundary tests precede fitting. The
native judge is not part of unchanged-source reconstruction. Existing judge/lane
test availability is reported, not silently treated as a qualification pass.
Independently decode all final packets and bind each to original exact source
hashes. Preserve all coverage failures. Human effort, autonomous solving,
fresh correctness, 1,000 problems and compact-library M1 are separate goals.
