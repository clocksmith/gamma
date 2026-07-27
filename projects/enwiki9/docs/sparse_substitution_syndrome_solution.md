# Solution to Independent Problem SS-1

Status: `COMPLETE INTERNAL SOLUTION`

At any position \(i\) with \(a_i\ne b_i\), a script that contains no
instruction at \(i\) leaves symbol \(a_i\) unchanged and cannot produce
\(b_i\). Thus every mismatch position requires an instruction.

The script

\[
\{(i,b_i):a_i\ne b_i\}
\]

changes every mismatch to its target value and leaves every match untouched.
It is valid and has one instruction per mismatch. The lower bound above proves
minimum cardinality \(d_H(a,b)\). Since a valid minimum script cannot contain
an instruction at a matching position or a second instruction at any position,
its position-value pairs are forced. Increasing position order makes the
representation canonical.

For prototype \(a_j\), the minimum cost is

\[
d_j+c\,d_H(a_j,b).
\]

Taking the least value over the finite family gives the global prototype
optimum; the supplied order resolves ties.

When target blocks have independent framing and disjoint payloads, every
choice changes only its own block cost. The total objective is separable, so
choosing the cheapest legal representation independently in each block is
globally optimal.

A certificate lists the chosen prototype and increasing mismatch pairs for
each selected block. The verifier compares all \(L\) prototype and target
positions, checks that the listed support is exactly the mismatch support,
checks every replacement value, and recomputes all candidate costs. Direct
verification costs \(mL\) symbol comparisons plus one pass over the selected
script.
