# Native expert disagreement mixture

Owner `root_expert_mix`; candidate `fx2_expert_mix_opening250k_v1`.
This is one bounded development mutation of the existing native FX2 predictor.
The active objective remains 90,000,000 complete bytes; full-corpus score is unknown.

The preceding paid-odds experiment found only 144.259854 gross ideal bits in
its exactly optimized seven-choice final-probability family, less than its384
table bits. It did not inspect the parent model's constituent expert outputs.
This successor tests those additional causal inputs, preserving every parent
prediction and online update. It neither revives the retired fixed ratio
calibration nor changes the pretrained transformer or its article resets.
The public RATA description also identifies expert-conditioned correction as
an architectural direction ([benchmark](https://mattmahoney.net/dc/text.html)).
This independently implemented mixture is not a novelty or superiority claim.

Deliberately select discovery lenses 8/9: causal adaptation and expert mixtures.
The tested premise is that which experts disagree with the parent can identify
different useful mixtures. Rejecting final-confidence calibration alone does
not test this premise. One configuration, exposed opening 250KB, no tuning or
confirmation in this gate. Parent ancestry and the prior paid-odds reflection
are immutable contract inputs. Other meaningful alternatives considered here:
repeating WRT support normalization is not selected (native fixture saved 2
bytes and did not pay its package); no deep teacher port is authorized by this
experiment. Exact weight packing remains independent from payload improvement.

Let p be the existing final bit-one count, and e1,e2,e3 the current PPMd,
neural byte-mixer and final FXCM counts, all with denominator 65536. The four
component counts are p and floor((3p+ei+2)/4). The context is the current
MSB-first bit position times 8 plus the three indicators ei>p. Each of 64
contexts has four positive integer weights summing to 2^32. Initialization
assigns approximately one half to p and one sixth to each other component.
The returned count is the rounded weighted mean, ties upward.

After observing the decoded bit, multiply each weight by that component's
truth count. Renormalize to 2^32 with minimum weight 1, largest remainders,
and lowest-index ties, using unsigned 128-bit intermediates. All parameters
and arithmetic are specified in the delivered source; no fitted table or
parent probability file is required by the native encoder or decoder.
Forced byte-mixer predictions are preserved. No corrected count is fed into
the parent's learning. Standard ideal Bayesian-mixture bounds motivate this
design but are not asserted for its rounded finite implementation.

P emits the unchanged parent. K computes the D mixture and updates it while
emitting P counts. D emits aligned mixture counts. S replaces each expert by
its value eight bit events earlier, preserving bit position; it uses parent
features for the first byte. S therefore delays information rather than
renaming a grouping or complementing a recalibrated donor. This tests alignment
against that specific delay, not every alternative explanation or delay.

All four arms independently encode, decode and reencode the same original
raw bytes. P/K archives and coder records must match the retained native P.
Every parent pre-quantization float prediction and decoded truth must match
across arms. K and D adapter state must match, and each arm's encoder, decoder
and repeat must match all adapter state at every 2,048 bits and termination.
State includes all256 weights, delayed expert triples and clock; padding and
arm labels are excluded from serialization. A separate D encoding without
instrumentation must produce the same archive. Other parent states follow
unchanged source and identical observed truths; they are not fully serialized.

If initial states agree, both sides compute the same captured expert outputs,
context, integer mixture and decoded bit. The specified update preserves
agreement by induction. This proves synchronization of the defined transition;
the independent native inverse checks test its implementation. It does not
prove a smaller archive.

One restricted bound does hold. Write v for normalized posterior weights and
alpha=(2^32-4)/2^32. The integer update satisfies v'_i>=alpha*v_i*c_i/M,
because 1+floor((2^32-4)*v_i*c_i/M) is at least its argument, and remainder
allocation can only add. Telescoping within a context gives product(M_t)
>=v_initial,parent*alpha^(n-1)*product(p_t). Since the initial parent weight
is at least one half, the ideal loss of the weighted mean before count
rounding is at most one bit per visited context plus
(n-1)*log2(1/alpha). Summing contexts yields at most 64+N*log2(1/alpha) bits.
This protects the unrounded mixture relative to the parent on the same events;
it is not a gain guarantee. Final Q16 rounding, arithmetic-interval rounding,
termination and package bytes are excluded from that bound and remain charged
by the actual native archive comparison. It does not prove a 90M representation.

Report actual P-D and S-D archive differences separately from added source,
binary and option bytes. Shared models and dictionary remain counted in the
package inventory. Source/binary component sums are overlapping sensitivity
figures, not an accepted official package. A positive comparison that does not
pay those increments may be held for a smaller delivery representation, but
does not automatically authorize a larger corpus. Resource, correctness and
incomplete-evidence failures remain separate from a valid compression loss.

Execution closed under job `20260914T213312Z_f00d023011`, with all 16 phases
passing. [Terminal receipt](../operations/provenance/fx2_expert_mix_terminal_20260914.json)
and [validated reflection](../operations/adaptive/reflections/20260914T213312Z_f00d023011.json).

| Arm | Actual archive bytes |
| --- | ---: |
| P, unchanged parent | 33,429 |
| K, bookkeeping | 33,429 |
| D, aligned expert mixture | 33,395 |
| S, eight-bit-delayed experts | 33,436 |

D saves 34 archive bytes versus P and 41 versus S on this exposed population.
Every arm passed independent inversion and deterministic repeat, with 591 state
boundaries per process. P/K match the retained native archive and coder trace;
K/D adapter states match. All parent float predictions and observed truths are
identical across arms. D trace-free encoding produces the same archive.
Both source builds produced identical binaries. 154 frozen inputs and all closed
artifacts were rehashed at closure. Peak cgroup memory was 6,308,003,840 bytes;
scratch peaked 444,071,936 allocated and 15,120,155,662 logical bytes, the latter
including the sparse PPM file. All guard measurements and cleanup passed.

The experimental source increment is 7,507 bytes, binary increment 16,384 bytes,
and option increment 24 bytes. Their overlapping local component sensitivity is
23,915 bytes, leaving a 23,881byte deficit after the 34-byte archive saving.
This is not a complete or accepted submission score. It is a positive native
predictive result that does not yet pay the measured experimental delivery.
The fixed predictor is held for a smaller production delivery and separately
frozen confirmation, with no automatic larger-corpus authorization. No change
to calibration, contexts or mixture strength is justified by this result alone.

The conclusion is limited to this implemented native mixture and delayed
control on exposed opening 250KB. It does not establish novelty, superiority on
unseen data, cross-machine eligibility or a 90M full-corpus witness.

## Compact production delivery

The [production closure](../operations/provenance/fx2_expert_release_terminal_20260915.json)
passes all 11 phases at `fx2_expert_release250k_v3`: two source builds per arm,
preprocessing, independent P/D inverses and repeats. P remains 33,429 bytes;
D remains 33,395 bytes, identical to the experimental mixture archive.
No runtime arm selector or research observer is required by this delivery.

Removing the unused LSTM implementation and reducing the mixture to its
production operations changes the executable from 483,848 original bytes to
438,792 for trimmed P or 442,888 for D. Against original delivery, D saves
40,960 executable bytes plus the measured 34 archive bytes. Against an equally
trimmed P, the mixture adds 4,096 executable bytes: its local component net is
negative 4,062 bytes. Trimming and predictive improvement are separate effects.

The complete source ZIP comparison is original 3,910,568, trimmed P 3,905,220,
and D 3,906,387 bytes. D adds 1,167 over trimmed P plus 21 required compiler
option bytes, yielding negative 1,154 local archive-plus-source bytes. Against
original source delivery that same alternative saves 4,194 component bytes.
ZIP and executable comparisons are alternatives, never summed together.
Models, dictionary, licenses, dependencies, option closure and official
multiplicities still require full package qualification. No full-corpus credit.

Two earlier build-only failures are retained with validated reflections:
removed LSTM make prerequisites and lost transitive iostream includes. Neither
ran a corpus comparison. Version 3 adds explicit includes and preserves the
same production arithmetic. The exact release is held for independent
confirmation and packaging; no larger launch follows automatically.

The [delivery selection](../operations/provenance/fx2_release_delivery_selection_20260915.json)
favors trimmed P under both measured component forms: 45,056 archive-plus-one-
executable bytes saved against original, or 5,348 archive-plus-one-source-ZIP
bytes. D saves 40,994 or 4,194 respectively. Thus adding the measured mixture
makes this sample's complete measured component total worse than trimming alone.
Prefer the immutable trimmed P for a separately frozen release confirmation;
retain D as a local predictive result whose extra delivery is not yet paid.
Neither alternative is a complete submission score, and neither transfers its
savings to the rejected learned-head experiments.
