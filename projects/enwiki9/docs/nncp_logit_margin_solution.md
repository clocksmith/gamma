# NL-1 Solution: The Multiclass Logit-Margin Certificate

## 1. Exact perturbation envelope

Write

\[
Z=\sum_i e^{z_i}.
\]

Then

\[
\begin{aligned}
\ell(z+\delta,y)-\ell(z,y)
&=
\log_2
\frac{\sum_i e^{z_i+\delta_i}}{\sum_i e^{z_i}}
-\frac{\delta_y}{\ln2}.
\end{aligned}
\]

Let

\[
\delta_{\min}=\min_i\delta_i,
\qquad
\delta_{\max}=\max_i\delta_i.
\]

Because

\[
e^{\delta_{\min}}Z
\le
\sum_i e^{z_i+\delta_i}
\le
e^{\delta_{\max}}Z,
\]

we obtain

\[
\boxed{
\frac{\delta_{\min}-\delta_y}{\ln2}
\le
\ell(z+\delta,y)-\ell(z,y)
\le
\frac{\delta_{\max}-\delta_y}{\ln2}.
}
\]

The upper bound is symbol-specific and invariant under adding a common
constant to every logit.

## 2. Oscillation and uniform bounds

Since \(\delta_y\ge\delta_{\min}\),

\[
\delta_{\max}-\delta_y
\le
\delta_{\max}-\delta_{\min}
=
\operatorname{osc}(\delta).
\]

Therefore

\[
\boxed{
\ell(z+\delta,y)-\ell(z,y)
\le
\frac{\operatorname{osc}(\delta)}{\ln2}.
}
\]

If

\[
\|\delta\|_\infty\le\varepsilon,
\]

then

\[
\operatorname{osc}(\delta)\le2\varepsilon,
\]

so

\[
\boxed{
\ell(z+\delta,y)-\ell(z,y)
\le
\frac{2\varepsilon}{\ln2}.
}
\]

## 3. Sharpness

Take two classes. Let the true class be \(y=1\), set

\[
\delta_1=\delta_{\min},
\qquad
\delta_2=\delta_{\max},
\]

and let the unperturbed competitor logit exceed the true-class logit by a
quantity tending to \(+\infty\). The log-sum-exp ratio then approaches
\(e^{\delta_{\max}}\), while the true-logit term contributes
\(-\delta_{\min}\). Hence the excess loss approaches

\[
\frac{\delta_{\max}-\delta_{\min}}{\ln2}.
\]

The oscillation coefficient cannot be decreased universally.

## 4. Archive-margin threshold

For symbols \(t=1,\ldots,N\), suppose

\[
\|\delta_t\|_\infty\le\varepsilon.
\]

The cumulative ideal excess is at most

\[
\frac{2N\varepsilon}{\ln2}
\]

bits, or

\[
\frac{N\varepsilon}{4\ln2}
\]

bytes.

Let \(R\) bytes bound every additional difference between ideal code length
and the two concrete arithmetic archives, including frequency quantization,
termination, framing, and any changed block boundaries. A sufficient condition
for staying inside an \(H\)-byte margin is

\[
\frac{N\varepsilon}{4\ln2}+R\le H.
\]

Thus, when \(H>R\),

\[
\boxed{
\varepsilon
\le
\frac{4(H-R)\ln2}{N}.
}
\]

If \(H\le R\), this certificate provides no positive uniform approximation
budget.

Using a direct oscillation bound

\[
\operatorname{osc}(\delta_t)\le\omega
\]

instead gives the sharper sufficient condition

\[
\boxed{
\omega\le\frac{8(H-R)\ln2}{N}.
}
\]

## 5. Affine-output approximation

For output row \(i\),

\[
\begin{aligned}
|z_i-\widehat z_i|
&=
|(W_{i,:}-\widehat W_{i,:})h+b_i-\widehat b_i|\\
&\le
\|W_{i,:}-\widehat W_{i,:}\|_2\|h\|_2
+|b_i-\widehat b_i|\\
&\le
\eta S+\beta.
\end{aligned}
\]

Therefore

\[
\boxed{
\|z-\widehat z\|_\infty\le\eta S+\beta.
}
\]

For \(N\) symbols, the cumulative ideal archive penalty is at most

\[
\boxed{
\frac{N(\eta S+\beta)}{4\ln2}
\text{ bytes}.
}
\]

This certificate applies only when the same hidden vector \(h\) is supplied to
both output layers. If approximating earlier layers changes \(h\), their state
error must also be propagated.

## 6. Layerwise propagation

Let the exact recurrence through \(L\) layers be

\[
x_j=F_j(x_{j-1}),
\]

and the approximate recurrence be

\[
\widehat x_j=\widehat F_j(\widehat x_{j-1}).
\]

Assume

\[
\|F_j(u)-F_j(v)\|\le K_j\|u-v\|
\]

and

\[
\sup_x\|F_j(x)-\widehat F_j(x)\|\le e_j.
\]

Writing

\[
d_j=\|x_j-\widehat x_j\|,
\]

the triangle inequality gives

\[
d_j\le K_jd_{j-1}+e_j.
\]

Iteration yields

\[
\boxed{
d_L
\le
\left(\prod_{j=1}^{L}K_j\right)d_0
+
\sum_{i=1}^{L}
e_i\prod_{j=i+1}^{L}K_j.
}
\]

If the final logit map is \(K_{\mathrm{out}}\)-Lipschitz into
\(\ell_\infty\), then

\[
\varepsilon
\le
K_{\mathrm{out}}d_L+e_{\mathrm{out}}.
\]

Substituting this value into the archive-margin inequality gives an explicit
sufficient implementation-error budget.

For a recurrent or online-trained model, this propagation must include every
state and parameter update. Treating each symbol independently is invalid.

## 7. NNCP transfer boundary

The published NNCP total leaves a nominal margin

\[
H=108{,}000{,}000-107{,}261{,}318
=738{,}682
\]

bytes, conditional on reproducing that accounting.

NL-1 converts an exact symbol count \(N\), coder budget \(R\), state bounds,
layer constants, and kernel approximation errors into a sufficient loss
budget. It does not establish any of those antecedents.

A prize-bearing transfer still requires:

- exact reproduction of the published archive and complete package;
- deterministic CPU encode and decode;
- exact integer or otherwise reproducible probability semantics;
- native arithmetic bytes, not ideal loss alone;
- self-contained source and model accounting;
- official runtime, memory, and disk compliance;
- exact roundtrip and deterministic artifact hashes.

The theorem can reject an unsafe approximation before a full run or certify a
conservative error envelope. Only the native complete archive determines the
score.

