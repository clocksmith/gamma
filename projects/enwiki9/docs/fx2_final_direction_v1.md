# Fixed recorded probability path

This diagnostic concerns the closed opening250KB P/D and P/S traces. It does
not change a codec, transmit a coefficient, or establish a finite archive size.
The prospective bounds and exact inputs are in the
[plan](../operations/provenance/fx2_final_direction_v1_plan.json).

For each recorded bit let `p=P_count/65536`, `q=arm_count/65536`, and truth `y`.
Both counts are in1..65535. Fix `delta=logit(q)-logit(p)` and define
`r(alpha)=sigmoid(logit(p)+alpha*delta)` for real `alpha`.
Let `G(alpha)` be summed log likelihood under `r(alpha)` minus that under `p`,
measured in nats. Differentiating gives

```text
G(0) = 0
G'(0) = sum((y-p)*delta)
G''(alpha) = -sum(r(alpha)*(1-r(alpha))*delta*delta) <= 0
```

Consequently, an upper bound `G'(0)<=0` proves `G(alpha)<=0` for every
`alpha>=0` on this fixed analytic path. A strictly positive lower bound proves
that some positive neighborhood improves ideal log likelihood. Neither result
alone proves an improvement in a quantized arithmetic archive.

The implementation aggregates exact integer coefficients of `ln(n)` for
`1<=n<=65535`; there is no floating point accumulation in the certificate.
For an event, weight `65536*y-P_count` multiplies the arm-count logit and its
negative multiplies the parent-count logit. Expand each logit as
`ln(count)-ln(65536-count)` and collect equal logarithms.

Python documents `Decimal.ln` as correctly rounded with ROUND_HALF_EVEN;
the installed runtime exposes the same contract in its method documentation.
See [the primary documentation](https://docs.python.org/3.14/library/decimal.html#decimal.Decimal.ln).
Here logarithms are evaluated at80 significant digits. Since their magnitude
is below12, rounding error is below10^-77. The exact rational representation
of each returned Decimal is scaled by10^40 and floored using integer division.
If that integer is `k`, `[k-1,k+2]/10^40` encloses the mathematical logarithm.
Signed integer interval multiplication and addition then enclose `G'(0)`;
the reported numerators and positive denominator are the authoritative bounds.
An approximate bit-unit rendering is diagnostic only.

The certificate assumes the documented Decimal contract and correct execution
of the retained source. Synthetic tests compare independent direct expressions
at140 digits, test known signs and exact cancellation, and reject malformed
trace alignment. Both full computations must produce identical witnesses.

Scope matters: these endpoints are the recorded Q16 probabilities. Their logit
interpolation is not identical to scaling the native odds multiplier before
its original rounding. The result therefore does not exclude every weakened
native rule, online strength selection, another information source, another
population, or finite-coder effects. Package costs remain unpaid.
