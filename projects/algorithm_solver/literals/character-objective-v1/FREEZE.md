# Character-aware dictionary objectives

Board18, goal2a. Item16 found1.60% character-count tie headroom for control256 and
similar headroom for scope_joint256, with no128headroom. Test whether explicitly
penalizing fallback codes during dictionary search improves the action/character
tradeoff. This changes an offline search/encoder objective, not M1 or input charges.

## Frozen population and arms

Fix all sources to item13 scope_joint256's selected fit300/validation100 bytes;
reuse its hash-bound qualification without new source execution. This seed was
selected using consumed validation outcomes; this is adaptive development, not
confirmation. No new source naming or alternatives under the new dictionaries.
Final held-out100/protected66 stay closed. No corpus searches/measurements before
this freeze. Six focused tests cover100 exhaustive tiny encodings x4weights,
weight tradeoffs, zero-weight ties, exact-cache parity, pruning, proposal legality,
bounded refill/search and retained incumbents.

Five dictionaries: `seed` fixed item13 dictionary and four equal-budget searches
`w0`,`w1`,`w4`,`w16`. Each starts from the same seed and fixed fit sources. Minimize
integer objective4N+wC (lambda=w/4), tie by N,C,raw package bytes. Each source is
exactly segmented for (4N+wC,N,C), then lexicographic dictionary IDs. Thus w0 uses
minimum selections with minimum characters as secondary criterion; it is a new
matched continuation, not an assertion of identical canonical tie paths.

Keep96fallback characters and at most256entries, using the existing alphabet
then lexically sorted learned entries. Prune only unused learned entries, retaining
objective/N/C. Refill then the matched80-v3-style exact deletion/addition/swap/pair
neighborhood:96additions,500swaps,16pair-addition shortlist,8pair-removal shortlist,
150pairs; refill shortlist24. Candidate strings merge2–6current selected parts,
<=160bytes, witnessed by at least two distinct fit owners, excluding every complete
source/solve definition/body/trimmed body. Rank by summed weighted merge gain,
then byte length and text. Exact deletion harm/addition gain screens swaps/pairs;
all accepted moves are full-fit exact objective improvements, or lexicographic
ties improving N,C,package. Rank used for screening is not a proof of global search
optimality. Reuse cached parses only if no changed dictionary fragment occurs in
the fixed source. No training or learned scorer.

Each searched arm has12000dictionary evaluations or600seconds; retain the legal
incumbent at caps and report stop/trial/time/move counts. Four workers oncores0–7,
4GiBperprocess,1800-second global ceiling,PYTHONHASHSEED0. The seed runs no search.
Seal dictionary/fit hashes before loading validation values. No validation refit,
source choice or repair. Audit whole-source/body entries against both splits;
an illegal validation overlap invalidates that arm without repair.

## Three charged views per dictionary

Encode all400programs with canonical minimumN/ID, shortest_min_char, and its own
weighted policy; the seed's weighted policy hasw0. Independently decode all6000
packets. Assert canonical sequence parity with the current encoder and weighted
fit objective equals the optimization receipt. Source qualification is reused by
exact hash; output packet hashes bind each distinct encoder policy. No existing
canonical encoder or packet is overwritten. All dictionaries/sources/sequences/
traces stay private; public reports contain only aggregate and per-ID metadata.

Report source bytes, qualification, coverage, selection/action distributions,
<=32/96, absoluteC and code/payload-bit fraction, paired better/same/worse,
dictionary/packet/framing/padding,raw/decoder-inclusive package and offline encoder
source bytes. One Finish per program; fixed eight-bit codes; full runtime footprint
unmeasured. The weighted encoder can spend more actions to reduceC; its result
must never be reported as a canonical minimum-selection improvement. The canonical
and shortest_min_char views isolate the resulting dictionary's behavior under
common encoders. AbsoluteC minimization differs from minimizing C/N.

## Predictions and decisions

- W1: seed canonical reproduces item13 scope_joint256; all6000packets decode,
  hashes/qualification match and body audits are clean.
- W2: w0 does not increase fit minimum selections versus seed, and does not improve
  validation total actions by as much as1% under shortest_min_char.
- W3: at least one positive weight reduces validation absoluteC by at least10%
  versus w0 using each arm's weighted encoder, at no more than5% additional actions.
- W4: w16 weighted has fewer validation character codes and more actions thanw0.
- W5: no dictionary/policy meets every M1 cost indicator on consumed validation.

Report the validation Pareto frontier of total actions, absoluteC and package
bytes, including dominated arms and all failures. This frontier is descriptive
and does not replace medians,p95 or character-fraction thresholds. Keep existing
input readiness against pinned R/L-R256:100validation decode/qualify, clean audit,
>=5%actiongain,lower median/p90,>=60better and<=25worse,nonincreasingC/N,
package<=105%. Also report the same-policy seed contrasts, so a policy change
cannot masquerade as dictionary gain. Rank ready pairs by actions,package,arm,
policy, but any ready pair only motivates owner-approved separately frozen
confirmation. No M1 qualification or new independent-generalization claim.

Freeze/code/contract pushed then Claude review (or recorded PLAN30-minute timeout)
before launch. Component intent preserved; no production boundary, canonical codec,
ledger/catalog/claim change. Training,protected opening,publication,BITS deployment,
independent confirmation and human study remain owner-gated.
