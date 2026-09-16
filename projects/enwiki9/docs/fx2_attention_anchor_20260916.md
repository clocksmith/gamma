# Article-local attention retention

Candidate: `fx2_attention_anchor250k_v1`. One bounded mutation of the trimmed
native FX2 predictor; no full-corpus score, novelty or winning claim.

The paid residual family failed its opportunity bound and the finite causal
residual family failed its native archive comparison. The released mixture
retains an 11-byte distant gain but does not pay its measured implementation.
The previous 2048-window candidate regressed 631 bytes. None establishes that
retaining particular old states within the original capacity is useless.

The discovery cycle deliberately selects lenses 4 and 9: cache-state identity
and a distinct source of predictive information. No random selection is claimed.
Three hypotheses were considered: (1) final-coder gradient learning, deferred
because the actual quantized SSE map is piecewise constant and no surrogate is
specified; (2) zero-support correction, rejected because the neural distribution
already has a 1e-6 floor and native WRT constraints were already tested; (3)
same-capacity article-anchor retention, selected for one native comparison.
These are three reasoning passes by the same author, not independent review.

The external motivation is [StreamingLLM](https://arxiv.org/abs/2309.17453).
It reports that retained initial states help certain streaming language models.
It also changes position handling. Our fixed mutation keeps the existing
post-RoPE keys and absolute rotations, so it is not a reproduction of that
algorithm and inherits none of its results. No external code is incorporated.
The linked upstream implementation has an MIT license; the native parent keeps
its existing license and source attribution.

## Frozen mechanism

All three full-attention layers keep 1024 existing slots and the same paid
weights. Nine KDA layers, article resets, rotations, arithmetic kernels, PPM,
frontend and persistent mixer update rules remain unchanged. Different neural
predictions may intentionally change the downstream mixer trajectory.

P is the unchanged parent. K calls the new slot function in mode 0 and must
reproduce the complete parent archive and neural stream. D retains inputs 0..3
of each article and rotates the other 1020 slots. S retains inputs 4..7 instead,
using the same capacity and arithmetic. S tests early-position specificity;
it is not a claim that those four later inputs contain no useful information.

For zero-based article input t, D writes slot t before t=1024 and thereafter
4+((t-1024) mod 1020). S writes slot t before 1024; thereafter let
r=(t-1024) mod 1020 and write r for r<4, otherwise r+4. No new mutable counter
or transmitted state is introduced. The existing article counter resets.

Induction proves that after each insertion D contains the first four inputs
and the most recent 1020 remaining inputs, once full. S has the analogous
property for inputs 4..7. Before filling, both contain exactly the decoded
prefix. The cyclic mapping is a bijection over the unpinned slots, so capacity
never exceeds 1024 and no future or cross-article state is read. Encoder and
decoder start identically and compute the same slot from decoded history;
identical updates therefore imply identical next probabilities. These are
state/inversion properties, not size guarantees.

An independent chronological queue test checks the native helper at every
position for article lengths 0,1,4,8,1023,1024,1025,2045,8193,131072 in all
three modes. Native probability rows before 1024 preceding article inputs
must match P. Full neural repeats and P/K archives must match bytewise.
Full model state and decoder neural streams are not serialized; no such
stronger state-witness claim is made.

## Population, costs and decision

One exposed cold opening raw interval [0,250000), 151210 transformed bytes,
unchanged dictionary pretraining. No confirmation data, parameter fitting,
anchor-count search, position rebasing or parent-trajectory rescue. Retained
article boundaries give 117360 post-window opportunities, not savings.

32 outer phases cover four arms: eight builds, seven cleans, one preprocessing
check and sixteen codec operations. Every arm independently decodes, re-encodes
the restored raw input, repeats neural rows, and encodes without observation.
Actual archives decide compression; a neural-loss improvement is insufficient.

Report gP=P-D, gS=S-D, source ZIP increment plus the required mode flag, and
alternative executable increment. Models, dictionaries, runtime, licenses,
official multiplicities and full submission remain separate unresolved costs.
Only gP>0, gS>0 and positive source-component net, with all required checks,
authorize unchanged independent confirmation. An unpaid positive gain is held.
A valid nonpositive archive/control margin retires this fixed realization.
No sign, anchor-count or position sweep follows this gate. Correctness or
resource failure is incomplete evidence, not compression failure.

CPU2, cgroup memory 9999998976 bytes, swap zero, scratch 16000000000 bytes,
aggregate wall limit 3600 seconds. Hold execution behind the existing auxiliary
decoder repair, publish ownership, then obtain fresh resource admission.
The 90M complete-byte objective remains unproved and receives zero credit here.
