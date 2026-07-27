# Problem MV-2: Exact Capacity Allocation

Let there be finite tables \(i=0,\ldots,n-1\). Table \(i\) has a full
allocation \(M_i\in\mathbb Z_{>0}\) and a finite ordered set of legal divisors
\(D_i\). Choosing \(d_i\in D_i\) costs

\[
R_i(d_i)=M_i/d_i
\]

bytes and incurs an integer penalty \(L_i(d_i)\). Assume every listed divisor
divides \(M_i\). Given a memory budget \(B\), solve the following independent
finite problem.

1. Construct the lexicographically first vector \(d\) minimizing
   \(\sum_i L_i(d_i)\) subject to \(\sum_i R_i(d_i)\le B\).
2. Prove the construction is exact and finite.
3. Give an exact dynamic-programming recurrence and a Pareto-frontier
   reduction that preserves every possible optimum.
4. Extend the result to an uncertain measured penalty interval
   \([\underline L_i(d),\overline L_i(d)]\), minimizing worst-case total
   penalty.
5. For a fixed reference vector \(d^0\), construct the least lexicographic
   binary-divisor subset whose exact allocation saving is at least \(S\).

The problem concerns only finite integer objects. It makes no monotonicity
assumption about measured resident memory or prediction quality.

## Frozen FXCM instance

For `ContextMap2`, initialization with nominal size \(m_i\) allocates
\(M_i=2m_i+16,384\) bytes. The additive alignment term is unchanged by a
divisor, so changing divisor one to divisor two saves exactly \(m_i\) bytes.

The reference already halves index 13. The required additional mature-scope
allocation saving is at least 737,487,872 bytes. Determine whether additionally
halving indices

\[
\{5,7,8,9,10,11,12,14,15,16,17\}
\]

meets that requirement, using the source-declared nominal sizes.
