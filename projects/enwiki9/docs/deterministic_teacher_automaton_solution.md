# DTA-1 Constructive Solution

## Transition closure

For each pair \((q,a)\), let

\[
n_{q,a,j}
=\#\{t:z_t=q,\ x_t=a,\ z_{t+1}=j\}.
\]

The total disagreement count is a sum of independent cell costs:

\[
\sum_{q,a}
\left(
\sum_j n_{q,a,j}-n_{q,a,\delta(q,a)}
\right).
\]

Each cell is therefore minimized by selecting a state \(j\) of maximum
count. Choosing the smallest such \(j\) makes the table canonical.
An unobserved cell uses the self-loop \(q\).

## Closed-loop outputs

Starting from the fixed initial state, run \(\delta\) over the training
symbols to obtain decoder-visible states \(q_t\). For one state \(q\),
define

\[
R_q(a)=\sum_{t:q_t=q}r_t(a).
\]

Writing \(W_q=\sum_aR_q(a)\) and
\(\bar R_q=R_q/W_q\), the cross entropy satisfies

\[
-\sum_aR_q(a)\log p(a)
=W_qH(\bar R_q)+W_qD_{\rm KL}(\bar R_q\Vert p).
\]

Thus the unique real-valued optimum is the teacher centroid
\(\bar R_q\). A state absent from the closed-loop path uses the global
training centroid.

## Exact integer outputs

After assigning one count to every symbol, the gain from assigning the
next count to symbol \(a\) is

\[
R_q(a)\log\frac{k_a+1}{k_a}.
\]

These marginal gains decrease as \(k_a\) grows. Selecting the largest
available gain at each step chooses the maximum-weight prefix-closed
set of \(M-V\) increments. An exchange argument replaces any selected
smaller gain by an available larger gain without violating prefix
closure. The greedy table is therefore globally optimal. Symbol order
breaks ties canonically.

The hard control replaces \(r_t(a)\) with
\(\mathbf 1[x_t=a]\) while retaining every other object.

## Causality and roundtrip

Before the first coded symbol, encoder and decoder use the same shipped
state. Assume their states and decoded prefixes agree before symbol
\(t\). They select the same integer output table and therefore perform
inverse updates on the same arithmetic interval. The decoder recovers
\(x_t\). Both then apply the same table lookup
\(\delta(q_t,x_t)\), so their next states agree. Induction proves exact
state agreement and reconstruction for the whole stream.

## Accounting boundary

Serialize \(K,V,M\), the initial state, the complete \(K\times V\)
transition table, and all \(K\) integer output tables in fixed order.
The archive contains the decoded length, any conservative seed state,
and the finalized arithmetic payload.

\[
S_{\rm student}
=|{\rm compressed\ model}|+|{\rm framing}|+|{\rm payload}|.
\]

Teacher labels, clustering loss, teacher ideal bits, and unshipped
probabilities receive zero score credit. A Hutter result additionally
requires a native full-corpus program, exact package accounting,
determinism, reconstruction, runtime, and memory qualification.

