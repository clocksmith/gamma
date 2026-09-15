# Causal residual projection on a protected parent

This separately frozen hypothesis asks whether local decoded errors predict later
errors, rather than buying a global coefficient table. Dense and sparse static
table rejections remain unchanged. Lenses 8 and 9 motivate a compact causal state
and a final-coder comparison. No teacher MIDAS savings are inherited.

Use the verified native pre-truth ternary features and exact final Q16 counts on
exposed raw `[0,250000)` (151210 modeled WRT bytes). The source parent remains
the trimmed FX2 release. There is no native inference in this screening gate.

For each fixed 64 modeled-byte block, the first 32 bytes keep parent counts.
For each bit-position row, accumulate `m = sum(phi * (Q*y-c))`. Freeze it at the
midpoint. In the second half compute `psi = dot(m,phi)/sum(abs(m))`, or zero
when the denominator is zero. Reset at block end; a short tail learns only its
first 32 bytes and corrects any remaining bytes. No second-half update is used.

The control rotates first-half residuals by 17 byte positions within each row
before pairing them with the same first-half features. This preserves values,
capacity and availability while changing alignment. Control equality is measured,
never assumed. No fixed feature permutation is presented as a negative control.

One shared nonnegative amplitude `a` gives `q=p+p*(1-p)*a*psi`. The finite
development family is `a in {0,1/32,1/16,1/8,1/4,1/2}`. Parent probabilities
and learning do not depend on `a`. For `x=psi*(y-p)`, the ideal gain is therefore
`F(a)=sum(log(1+a*x))`, concave, and `F(a)<=a*G` with `G=sum(x)`.
Every `a in [0,1/2]` is bounded by `max(0,G)/2`. The implementation encloses G
by summing floor values on a common exact 2^-64 grid, adding one grid unit for
every nonzero term. It adds a conservative Q16 rounding allowance and uses the
previous exact rational ln(2) bound. This is an ideal-likelihood bound, not an
archive-length bound.

If the aligned rounded upper cannot pay 16 header bits, stop before finite
replay. Otherwise encode all six amplitudes for D and S. Each candidate pays a
version byte and an amplitude-index byte in addition to native framing/payload.
Select smallest complete conditional archive, tie-breaking by lower index,
separately for D and S. Zero correction, after stripping those two paid header
bytes, must be byte-identical to the native parent. This is P/K identity.

Rounding is nearest with exact half ties upward, clamped to 1..65535. Compute
`c' = round(c + c*(Q-c)*k*A/(Q*32768*M))`, where `a=k/32768`, `A=dot(m,phi)`
and `M=sum(abs(m))`. Missing features and M=0 produce zero correction. Python
integers are exact; a future native implementation needs signed 128-bit products.

Independently decode the selected D and S archives using only decoded truths
for controller updates. Verify the complete controller state at every byte,
every corrected count, canonical arithmetic termination, and exact WRT raw
inverse. Repeat the entire calculation in a separate subprocess and require all
artifacts byte-identical. The recorded truth field is ignored during decoding.

These are conditional archives: counts and feature records remain supplied
research dependencies, whose sizes are reported. The existing native observation
proved their causal origin; this gate does not regenerate them. Native integration,
complete code costs, source closure and independent confirmation remain required.
No score or full-corpus credit is granted. Promotion requires D to beat both P
and the best S after its two-byte header. A positive upper alone cannot promote.

Synthetic evidence covers aligned versus misaligned slopes, exact rounded
counts, complete-state arithmetic roundtrip, no second-half truth learning,
partial blocks, reset, deterministic replay, missing features and malformed
record rejection. Source and tests are frozen before corpus analysis.
