# Native expert disagreement mixture

Owner `root_expert_mix`; candidate `fx2_expert_mix_opening250k_v1`.
This is one bounded development mutation of the existing native FX2 predictor.
The active objective remains 90,000,000 complete bytes; full-corpus score is unknown.

The preceding paid-odds experiment found only144.259854 gross ideal bits in
its exactly optimized seven-choice final-probability family, less than its384
table bits. It did not inspect the parent model's constituent expert outputs.
This successor tests those additional causal inputs, preserving every parent
prediction and online update. It neither revives the retired fixed ratio
calibration nor changes the pretrained transformer or its article resets.
The public RATA description also identifies expert-conditioned correction as
an architectural direction ([benchmark](https://mattmahoney.net/dc/text.html)).
This independently implemented mixture is not a novelty or superiority claim.

Deliberately select discovery lenses8/9: causal adaptation and expert mixtures.
The tested premise is that which experts disagree with the parent can identify
different useful mixtures. Rejecting final-confidence calibration alone does
not test this premise. One configuration, exposed opening250KB, no tuning or
confirmation in this gate. Parent ancestry and the prior paid-odds reflection
are immutable contract inputs. Other meaningful alternatives considered here:
repeating WRT support normalization is not selected (native fixture saved2
bytes and did not pay its package); no deep teacher port is authorized by this
experiment. Exact weight packing remains independent from payload improvement.

Let p be the existing final bit-one count, and e1,e2,e3 the current PPMd,
neural byte-mixer and final FXCM counts, all with denominator65536. The four
component counts are p and floor((3p+ei+2)/4). The context is the current
MSB-first bit position times8 plus the three indicators ei>p. Each of64
contexts has four positive integer weights summing to2^32. Initialization
assigns approximately one half to p and one sixth to each other component.
The returned count is the rounded weighted mean, ties upward.

After observing the decoded bit, multiply each weight by that component's
truth count. Renormalize to2^32 with minimum weight1, largest remainders,
and lowest-index ties, using unsigned128-bit intermediates. All parameters
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
and repeat must match all adapter state at every2048 bits and termination.
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
(n-1)*log2(1/alpha). Summing contexts yields at most64+N*log2(1/alpha) bits.
This protects the unrounded mixture relative to the parent on the same events;
it is not a gain guarantee. Final Q16 rounding, arithmetic-interval rounding,
termination and package bytes are excluded from that bound and remain charged
by the actual native archive comparison. It does not prove a90M representation.

Report actual P-D and S-D archive differences separately from added source,
binary and option bytes. Shared models and dictionary remain counted in the
package inventory. Source/binary component sums are overlapping sensitivity
figures, not an accepted official package. A positive comparison that does not
pay those increments may be held for a smaller delivery representation, but
does not automatically authorize a larger corpus. Resource, correctness and
incomplete-evidence failures remain separate from a valid compression loss.

Execution outcome: pending prospective publication and admission.
