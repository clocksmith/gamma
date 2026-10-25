# Hard32 wave2 numerical comparator successor v2

This separate lane preserves the original482992d2freeze, old oracle, raw run,
and old verifier result. It does NOT retroactively certify the flawed numeric
conversion: Decimal(str(float)) uses a rounded decimal rendering, whose error
can exceed the1e-35 analytic guard. A synthetic regression demonstrates both
false acceptance and false rejection by that old conversion.

The successor uses Decimal.from_float for exact binary-float conversion and
Decimal(int) for integer-valued JSON numbers in the JavaScript numeric profile.
Python result_type remains float and requires an actual decoded float. Booleans,
NaN and infinities reject. Precision1200 permits exact finite-binary64 conversion
and subtraction from the bounded50-digit analytic optimum (including subnormal
values) without consuming the1e-35 guard through decimal-display rounding.
The official1e-5 absolute tolerance and analytic-oracle uncertainty are unchanged.
Fraction-based nextafter controls cover both tolerance boundaries around0,5,7000;
additional controls cover subnormal/maxfinite values and both rounding bugs.

All14candidate sources,3114cases per language, expected analytic values,
20singleton1515cases per language, all effects/limits/harnesses are unchanged.
New independent raw-observation revalidation or native replay is required before
adoption. No success is inferred from the old verifier verdict.

## Original wave design (same domains, new conversion supersedes old comparator)

# Hard32 wave2: seven public contracts, one explicit blocked pair

Requested wave IDs are1515,1521,1542,1585,1713,1788,2111,2127. The official1788
page requires Premium; no domain was invented and no alternate mirror was read.
Its two slots remain unqualified and blocked. The full32/64 worklist and original
4081/8162 catalogue denominator remain visible. This public subset independently
prepares14 owner-provided source-language pairs, not a claim of16/16 success.
No source file, author claim, canonical registry, or prior receipt is changed.

Seven official public descriptions were independently read2026-10-25 after the
live per-ID gate.1521's function is an image: the exact official asset was fetched
and visually reviewed; its SHA256 is recorded in contracts.json. The function
ANDs an inclusive nonempty interval; its invalid reversed interval sentinel
cannot minimize the distance to the nonnegative bounded target, because a valid
singleton is always strictly closer. No candidate-derived domain is substituted.
Official-review notes are reviewer paraphrases, not raw HTML or an official
signature. Their hashes establish only the exact reviewed local text.

Local interface: ordered positional solve, caller arguments unchanged, no result
aliases. These effect rules are local and identical across languages, not claimed
official mutation mandates. Results are exact typed scalars except1515, whose
public statement explicitly accepts absolute error1e-5. The comparator requires
a finite numeric result (Python float / JS number), then checks absolute error
against a conservatively guarded analytic oracle. It does not compare candidate
languages or require equal floating point encodings.

1515 host truth uses50-digit Decimal analytic formulas, NOT nested ternary search:
line medians, opposite-pair triangle lower bounds for central symmetry, majority
coincident-point triangle bounds, and the three-point Fermat/120-degree formula.
The longest calculation has only bounded50point sums and square roots of bounded
nonnegative values; the1e-35 uncertainty guard exceeds Decimal rounding error by
many orders. Unsupported geometry rejects; the candidate domain remains all
allowed50point instances. Tests include noncollinear scalene/obtuse triangles and
maximum-size symmetric families. Finite analytic fixtures do not prove all
geometry correct. Candidate source review separately checks convex minimization
inside the bounding box and80-by80 ternary refinement, with Lipschitz error
bounded in ideal arithmetic; floating arithmetic is assessed by finite tests.

Other host oracles: all interval ANDs; all substring digit counts; reachability
under adjacent inversion swaps (equivalent to substring sorting); full LCS table;
quadratic longest nondecreasing subsequences per residue; and exhaustive circular
seatings over chosen employee sets. Controlled maximum-size families have direct
mathematical expectations. Unsupported large host queries reject rather than
extrapolate. No historical cases, protected payloads, or developer tests are read.

Trusted code pins never read statement metadata. Combined notes/contracts/plan
reads are preceded by authorization for every included ID, and each source or
semantic sidecar has its own immediately preceding gate.1788 appears only as
metadata status; no locked statement/source is incorporated into this subset.

Runtime remains3CPU/8wall/1GiB/4MiB per isolated call, Node jitless/single-threaded
64MiB heap. Packing inherits the reviewed1.8MB packet /3.9MB conservative output
bound, at most32 cases, outer900seconds.1515 is PROSPECTIVELY frozen as singleton
batches in BOTH languages to avoid aggregating expensive nested numerical work;
this is declared before execution, not a retry-based budget increase. Every
synthetic case carries its batching marker, bound by the case hash. Maximum cases
are retained even if a real resource failure occurs. Parent owns native execution
after independent exact-freeze review and separately verifies/adopts results.
