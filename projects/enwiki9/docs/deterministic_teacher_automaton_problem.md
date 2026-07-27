# DTA-1: Deterministic Teacher-Automaton Closure

## Independent problem

Let \(A=\{0,\ldots,V-1\}\), let \(x_0,\ldots,x_{N-1}\in A\), and
let \(r_t\) be a strictly positive teacher distribution on \(A\).
Suppose a fixed canonical clustering rule assigns each training row a
teacher label \(z_t\in\{0,\ldots,K-1\}\).

Construct a finite student with:

\[
q_{t+1}=\delta(q_t,x_t),
\qquad
p_t=Q_{q_t},
\]

where the decoder receives only the initial state, transition table,
output tables, and previously decoded symbols.

Solve the following.

1. Among all deterministic transition tables, find one minimizing the
   number of training disagreements

   \[
   \#\{t:\delta(z_t,x_t)\ne z_{t+1}\}.
   \]

2. Run the selected transition table in closed loop over the training
   symbols. For each reachable student state, find the real-valued
   output distribution minimizing teacher cross entropy.

3. For an integer total \(M\ge V\), find the exact positive integer
   output table minimizing the same objective under

   \[
   k_a\ge1,\qquad \sum_a k_a=M.
   \]

4. Construct an equal-capacity hard-label control using the same
   clustering, transition table, closed-loop states, denominator,
   serialization, and arithmetic coder.

5. Prove that encoder and decoder states agree before every coded
   symbol and that exact arithmetic decoding reconstructs the sequence.

6. Give a canonical serialization and count transition, output,
   framing, and arithmetic payload bytes. State why teacher loss and
   teacher labels are oracle evidence rather than score credit.

