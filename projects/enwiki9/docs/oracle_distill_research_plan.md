# ORACLE-DISTILL: NNCP Residual Integer Compilation

Status: CURRENT CAUSAL TEACHER-QUOTIENT REALIZATION REJECTED / ZERO SCORE CREDIT

## Target

The selected Gamma planning forecast is 109,524,268 bytes. The design target is
108,000,000 bytes, leaving 1,524,268 bytes of debt.

Official NNCP v3.3 reports:

- archive: 106,632,363 bytes;
- program: 628,955 bytes;
- total: 107,261,318 bytes.

Relative to the selected Gamma forecast, the reported total-score gap is
2,262,950 bytes. A 256KB student retaining 80 percent of that gap would have
only a narrow path to the target. That is the explicit research threshold, not
evidence that such a student exists.

## External source binding

Official artifact:

`https://www.bellard.org/nncp/nncp-2024-06-05.tar.gz`

Downloaded artifact SHA-256:

`7b4be2a5871186b82cd5f1c6137a8f6fed0d0c6b2bb281793db1f0be65831119`

The source is MIT licensed. It builds on this machine using the supplied
`libnc.so`. No NVIDIA runtime is installed. The official documentation says
CPU execution is supported but a GPU is required for acceptable speed with
large models. Therefore the reported under-target result is teacher evidence,
not an eligible reproduced Gamma result.

## Gate 0: exact symbol/raw binding

The reported enwik9 profile uses a reversible dictionary preprocessor and
16-bit model symbols. The first gate must prove:

- exact preprocessor encode/decode roundtrip;
- each teacher symbol equals the corresponding preprocessed symbol;
- symbol raw intervals are ordered, gapless, and nonoverlapping;
- page boundaries are explicitly measured against symbol boundaries;
- the official tarball, observation patch, binary, dictionary, transformed
  symbols, map, input, and output are hashed.

The observation patch is:

`patches/nncp_symbol_raw_map_v1.patch`

The verifier is:

`tools/verify_nncp_symbol_map.py`

## Gate 1: teacher probability trace

Instrument the single official pre-coder distribution site immediately before
`write_sym`. Record:

- model symbol index;
- exact true symbol;
- normalized teacher distribution or a lossless sufficient representation;
- stream index and block position;
- exact arithmetic-coder bit count before and after the symbol;
- the Gate-0 raw interval.

The trace must reproduce the uninstrumented NNCP archive byte-for-byte on a
bounded scope. Teacher evidence remains zero-credit.

## Gate 2: representation compatibility

NNCP does not use Gamma's causal WRT bit order. Its preprocessor changes the
alphabet, and its model divides blocks across multiple streams. The gap map
must therefore separate:

- gain from reversible representation;
- gain from stream ordering;
- gain from the learned predictor;
- gain that is expressible from decoder-visible Gamma features.

Do not subtract the reported NNCP-Gamma score gap from Gamma. Do not train a
student until the expressible residual is measured.

## Gate 3: bounded integer student

Only after alignment and compatibility pass, test frozen students at:

- 64KB;
- 128KB;
- 256KB.

Permitted first representations:

- quantized oblivious decision trees;
- sparse factorization machine;
- tiny tensor-train residual table.

Promotion requires at least 80 percent retention of the measured aligned
teacher gap, 30,000 gross and 23,000 net bytes on canonical 10M, at least 2,000
bytes per million on offset-500M, deterministic exact replay, and eligible
memory/runtime.

## Kill conditions

Reject the route if:

- symbol/raw/page alignment is not exact;
- the advantage depends on unavailable stream reordering or teacher state;
- decoder-visible Gamma features cannot predict the advantage;
- every bounded student retains less than 80 percent after exact accounting.

## Claim boundary

NNCP's published result, symbol map, teacher traces, gap maps, and student
shadows receive zero score credit until a counted native Gamma codec produces
an exact archive, roundtrip, deterministic replay, package receipt, memory
receipt, and runtime receipt.

## Gate 0 and bounded Gate 1 receipts

Gate 0 passed:

`results/nncp_symbol_raw_map_opening_1m_v1/receipt.json`

The official preprocessor produced 753,198 symbols for the opening 1M. Its map
is exact, gapless, nonoverlapping, and reconstructs the raw input. All 171
complete page starts and ends occur on exact symbol boundaries. There are
12,755 zero-output symbols and 177,637 multi-byte symbols; the maximum raw span
is six bytes.

The bounded Gate 1 trace passed archive neutrality:

`results/nncp_teacher_trace_smoke_v1/receipt.json`

Trace-off and trace-on archives are byte-identical at 9,246 bytes. The trace
contains 10,000 unique symbols with continuous coder counts and finite true
probabilities. The guarded adjacent pair used 5,782,588 KiB peak tree RSS.

The compatibility result is adverse but not yet a terminal proof. NNCP used 32
streams; 9,999 of 10,000 execution rows differed from original symbol order,
with maximum displacement 9,672 symbols. The model updates after interleaved
multi-stream outcomes, so its mature prediction state is not automatically
reconstructible by a raw-order causal Gamma residual.

The mean true-symbol log loss at this bounded startup scope was 6.781875 bits.
This scope does not demonstrate NNCP's published mature advantage and cannot
support a student.

Next gate: separate representation and stream-order gain from predictor gain.
Do not launch an unchanged 1M CPU teacher run. A larger aligned teacher trace
requires either an eligible causal single-stream control or external
accelerated evidence with the exact patches and hashes bound here.

## Bounded single-stream causal control

Receipt:

`results/nncp_teacher_causal_smoke_v1/decision.json`

Using the same official `enwik9` profile and 10,000-symbol limit, changing only
batch size from 32 to 1 reduced the archive from 9,246 to 6,945 bytes. Reported
rate improved from 7.397 to 5.556 bits per teacher symbol. This shows that the
causal single-stream teacher is compression-positive at startup; stream
reordering is not required for this bounded gain.

The control is runtime-hostile. The batch-1 encode took 1,927.1691 seconds,
versus a 279.797-second mean for each encode in the adjacent batch-32 pair, a
6.887-times ratio. Tree RSS fell from 5,782,588 KiB to 1,857,532 KiB.

Decision: preserve batch-1 as offline distillation evidence only. Do not ship
NNCP, launch an unchanged larger CPU teacher, or claim the 2,301-byte bounded
control difference as Gamma gain. The next valid step requires an accelerated,
hash-bound causal teacher trace or a much smaller causal teacher whose residual
can be compiled into a counted integer student.

## Full-distribution causal trace and quotient decision

The true-symbol-only trace was insufficient for constructive distillation
because it did not define probabilities for alternative symbols. The
observation contract was upgraded to record all 336 normalized probabilities
before coding each true symbol:

`patches/nncp_teacher_distribution_trace_v2.patch`

The exact batch-1, 10,000-symbol trace is:

`results/nncp_teacher_causal_trace_10k_v1/receipt.json`

Trace-off and trace-on archives are both exactly 6,945 bytes with identical
SHA-256. The trace contains 10,000 sequential single-stream rows, all
distributions are positive and normalized, maximum normalization error is
`2.796e-7`, peak tree RSS is 1,857,536 KiB, and trace-on elapsed time is
1,905.8052 seconds. This is valid teacher evidence and zero score credit.

The exact common-boundary comparison is:

`results/nncp_gamma_gap_map_10k_v1/decision.json`

At the shared 13,310-raw-byte boundary, Gamma costs 22,661.711 bits while the
teacher true-symbol log loss is 49,408.720 bits. The causal NNCP teacher is
therefore 26,747.009 bits, or 3,343.376 bytes, worse on this startup
population. No student can improve Gamma by imitating this teacher here.

The fixed-budget quotient screen is:

`results/nncp_predictive_quotient_10k_v1/decision.json`

The 64KB quotient is the best of the predeclared budgets and retains only
29.242 percent of the teacher-over-unigram holdout gap. The 128KB and 256KB
budgets retain 29.215 percent because only 126 prior-symbol contexts occur in
training. Every budget fails the required 80 percent retention and its package
dominates the bounded payload.

Combined decision:

`results/oracle_distill_teacher_quotient_10k_v1/decision.json`

Reject the current official-NNCP CPU startup teacher-quotient realization. Do
not integrate it, enlarge the unchanged CPU run, or claim the teacher's
published full-corpus score as Gamma headroom. A materially different successor
requires an accelerated mature causal full-distribution trace or another
under-target teacher with an exact decoder-compatible representation.
