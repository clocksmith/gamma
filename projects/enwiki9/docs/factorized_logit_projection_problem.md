# FLP-1: Factorized Dyadic-Logit Projection

## Independent problem

Let \(A=\{0,\ldots,V-1\}\). For each time \(t\), let
\(x_t\in A\), let \(r_t\) be a positive teacher distribution, and let
\(F_t\) be a fixed set of feature identifiers computed only from
\(x_0,\ldots,x_{t-1}\).

For real table entries \(w_{f,a}\), define bit logits and probabilities

\[
z_t(a)=\sum_{f\in F_t}w_{f,a},
\qquad
p_t(a)=\frac{2^{z_t(a)}}{\sum_b2^{z_t(b)}}.
\]

Solve the following.

1. Prove that teacher cross entropy

   \[
   L(w)=-\sum_t\sum_a r_t(a)\log_2p_t(a)
   \]

   is convex in \(w\), and derive its gradient.

2. If every active table entry is quantized with error at most
   \(\eta\) and every row has at most \(m\) active features, prove an
   upper bound on per-row excess teacher cross entropy.

3. Give a deterministic finite training schedule, fixed tie rules, and
   an int8 model serialization. The mathematical claim is about the
   specified finite construction, not global optimality of its finite
   iteration count.

4. Construct exact positive integer probabilities from integer bit
   logits using a serialized dyadic exponential table and largest
   remainders.

5. Prove encoder/decoder feature, probability, arithmetic interval, and
   state agreement by induction.

6. Construct a hard-label control using the same features, training
   schedule, quantization, serialization, and coder. Count model,
   seed-history, framing, and arithmetic payload bytes.

7. State the transfer boundary: teacher loss is an oracle; only the
   shipped integer model and exact payload are constructive.

