# PCMF-1 Solution: Paid Conditional Multinomial Fibers

Each position has exactly one deterministic context, so the occurrence sets
\(I_c\) are disjoint and cover all positions.

For a fixed context, choose positions for each symbol in sequence. The
telescoping product of binomial coefficients is

\[
M_c=\frac{N_c!}{\prod_a n_{c,a}!}.
\]

In the without-replacement model, symbol \(a\) contributes successive
numerators \(n_{c,a},n_{c,a}-1,\ldots,1\), while all symbols share
denominators \(N_c,N_c-1,\ldots,1\). The probability of the complete
subsequence is therefore

\[
\frac{\prod_a n_{c,a}!}{N_c!}=\frac1{M_c}.
\]

At a binary-tree node, subtree-count ratios telescope along the path to the
chosen leaf. Its leaf probability is exactly the remaining symbol count over
the remaining context total. The complete sequence probability is unchanged.

Write

\[
w_c=P_c-d_c-\log_2M_c.
\]

Apart from the one shared frame, selected contexts affect disjoint occurrence
sets and have independent descriptions and type streams. Every positive
\(w_c\) increases the objective, every negative value decreases it, and zero
values are excluded by the inclusion-minimal tie rule. Thus the only
nonempty candidate is \(U_+=\{c:w_c>0\}\). Select it exactly when
\(\sum_{c\in U_+}w_c>h\); otherwise select the empty family. Context order
breaks any remaining serialization tie.

A certificate lists every context count vector, parent cost, description
price, type-class cost, contribution, selected bit, and the final sum. A
direct verifier scans the sequence once to reconstruct counts and costs, then
checks all context arithmetic. With \(|A|\) alphabet symbols, construction
uses \(O(n+|C||A|)\) time and \(O(|C||A|)\) count storage.

During decoding, the context before the current symbol is a function only of
the already reconstructed prefix. The decoder therefore knows whether to use
the parent or the selected context model. Both branches reconstruct one
symbol, which is then supplied to the parent update. Induction on position
proves equal contexts, code choices, predictor states, and output at encoder
and decoder.

The type-class identity is real-valued. A finite coder rounds each branch
ratio, emits renormalization bytes, and finalizes one or more streams. Exact
archive size and roundtrip must be established by integer replay.
