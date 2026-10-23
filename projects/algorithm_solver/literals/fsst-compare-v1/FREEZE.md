# Pinned FSST comparison and Gamma dictionary adapter

Board19, goals2a/5b. RESEARCH.md names FSST as an unrun practical comparator.
Measure the author implementation separately from adaptations to Gamma's literal
rules. This is one consumed-development population on one host; no M5/literature-
leading, throughput, human, autonomous-solving or independent confirmation claim.

## Implementation, fitting and sources

Author source: [cwida/fsst](https://github.com/cwida/fsst), pinned commit
`e638d4cf8c26129d73c242a4127b42b975de5b63`, MIT license. Its API maps1–8byte
symbols to byte codes and uses255 followed by a raw byte for an escape
([pinned header](https://github.com/cwida/fsst/blob/e638d4cf8c26129d73c242a4127b42b975de5b63/fsst.h)).
Native sources remain in a separate private checkout, not vendored or changed.
Compile libfsst.cpp/fsst_avx512.cpp plus the Gamma ABI wrapper with UbuntuG++15.2,
C++17,-O3,-DNDEBUG,-march=native,-fPIC,-shared. Pin source/header and resulting
library hashes. Native hardware compilation is for this host only; no portability
or performance qualification. No model weights, learned scorer or source export.

Two fixed-source cohorts from item13: control256 R and scope_joint256 naming.
Each uses the same qualified fit300/validation100 IDs; source/qualification,
dictionary and fit-source files pinned. Scope_joint was selected using consumed
validation outcomes. This is adaptive development. Final held-out100/protected66
stay closed. No Gamma corpus FSST fitting preceded this freeze. Eight focused
synthetic tests pass, including binary/zero/255bytes, both independent and author
decoders,100 exhaustive native-DP examples, repeatability, escape charges, malformed
frames, adapter owner/body rules and exact trial-cap retention.

For each cohort, call unmodified fsst_create on fit strings in ascending numeric
ID order, zeroTerminated=0. Use its default internal sampling/table construction,
without hyperparameter tuning or validation feedback. This is deterministic symbol-
table construction from the supplied corpus, not model training. Export and seal
the native table before any validation values are loaded. Retain the encoder
handle to encode validation without rebuilding it.

## Five views per cohort

1. `gamma_seed`: reproduce the cohort's recorded dictionary and canonical encoding.
2. `native_author`: native table and author fsst_compress payloads.
3. `native_optimal`: same table, exact minimum native payload bytes via a backward
   DAG; symbol edge costs1, raw-byte escape edge costs2; tie by payload byte IDs.
   This is Gamma's parser adaptation, not an asserted run of OptFSST.
4. `gamma_adapter`: extract native multi-byte symbols with at least two distinct
   fit-source witnesses, excluding complete sources/solve definitions/bodies/
   trimmed bodies. Rank by native fit code count*(symbol bytes-1), then shorter
   bytes and lexical text. Keep at most160, add all96Gammafallback characters,
   order with Gamma's canonical alphabet then learned strings, and encode by
   canonical exact DP. No native escape remains; <=256exact-string entries.
5. `gamma_polish`: start from that adapter and fit Gamma's exact refill/swap/pair
   search, restricted to the eligible native-symbol pool. Proposals retain the
   frozen native fit-gain order, excluding present entries; require two owners.
   Shortlist24refill;96additions/500swaps/16pairadditions/8pairremovals/150pairs.
   Cap5000exactdictionaryevaluations or300seconds. An isolated wrapper skips
   terminal pruning if the cap is reached, retaining a legal incumbent. No
   alphabet removal, native-pool expansion or source changes.

Seal all Gamma dictionaries and the native header/fit hash before loading
validation. Audit every dictionary/table against fit and validation whole-source/
body strings. Do not repair a validation overlap; it invalidates literal readiness.
Native remains a separate format regardless of that audit. Source hashes remain
unchanged and reuse prior strict qualification; no new execution/case opening.

## Complete charging and independent verification

For native views, each emitted byte is one eight-bit selection; an escaped raw
byte costs two selections. Both bytes of that escape count in the fallback-channel
subtotal, alongside one-byte native symbols. This diagnostic is labelled native
single-character-channel fraction, not Gamma literal-entry fraction. There are
<=255native symbols plus the escape control, but the conditional raw-byte operand
channel is a different codec, so native is never an M1 literal candidate.

Charge one Finish per program. Native packets have a strict41-byte wrapper:
FSN1magic,32-byte table hash,4-byte payload count and one fixed-width byte, followed
by the exact payload. Charge the exported FSST table bytes once, and compare raw
packages separately from Gamma's LTD1 table/41-byte packet format. Native strings
are decoded both through the author decoder and a strict independent Python
implementation. Native-optimal payloads must be no longer per program than author
payloads. Gamma packets use the unchanged canonical decoder. All4000packets
independently decode; source qualification is hash-bound reuse, not new evidence.

Report fit/validation separately: decoded/qualified coverage, source bytes,
selections/actions total,median,p90,p95,worst,<=32/96; paired gains; literal/native
fallback counts/fractions, raw escapes, table/packet/framing/padding, raw package
and decoder-source-inclusive package. Charge native.py+packet.py as the complete
independent decoder source files and the pinned Gamma decoder dependency files
for Gamma. Report the native shared-library binary and source tooling separately;
full Python/C++runtime installations are unmeasured. Source-inclusive sizes are
not complete executable deployment packages or an M5 storage qualification.
Store all source/table/sequence/traces privately and publish only metadata/hashes.

Two workers oncores0–3,4GiBaddress-space each,900-second overall ceiling,
PYTHONHASHSEED0. Report native table-build time and adapter-polish time/trials/stops
separately. No throughput winner inferred from these different work budgets.

## Predictions and readiness

- F1: seeds reproduce recorded counts; all4000packets decode/source hashes qualify.
- F2: native optimal is never longer per program than native author, and saves
  at least1%validation actions in at least one cohort.
- F3: Gamma polish saves at least5%validation actions over its adapter in at
  least one cohort.
- F4: neither Gamma adapter nor polish passes input readiness against its own
  matched source/dictionary seed. Native results are excluded from that decision.
- F5: no Gamma view meets all M1 cost indicators on consumed validation.

Literal readiness remains100validation decode/qualify, clean whole-solutionaudit,
>=5%fewer actions, lower median/p90,>=60better/<=25worse,nonincreasing literal
character fraction,package<=105%, against the cohort seed. Also show each Gamma
view against original R/L-R256 to separate old naming benefits from new dictionary
benefits. Rank any newly ready literal arms by actions,package,cohort,arm; native
never qualifies through that ranking. Any new candidate requires separately frozen
owner-approved confirmation before broader claims or protected access.

Freeze/code/contract pushed then Claude cross-review (or PLAN30-minute timeout)
before corpus fitting. Component intent preserved; no production or canonical
codec change, ledger/catalog/claim write, M1 threshold change, training, deployment,
private publication or human study. Existing owner gates remain.
