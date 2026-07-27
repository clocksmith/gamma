# LPF-1 Solution: Complete Causal Prior-Factor Cover

For any suffix rank \(r\), the LCP with another suffix rank is the minimum LCP
value between them in suffix-array order. If two previously inserted ranks
lie on the same side of \(r\), the nearer one uses a subinterval of the
farther one's LCP range, so its minimum cannot be smaller. Therefore the
largest LCP against the inserted set is attained by the immediate inserted
predecessor or successor of \(r\).

Choose the smaller source position on equal LCP lengths. This defines a
canonical source \(s_i\) attaining \(L_i\). Every legal copy of length
\(\ell\) proves \(\ell\le L_i\). Since \(s_i\) matches for \(L_i\) symbols,
its prefix of length \(\ell\) realizes the same command. Overlap is valid:
when copied left to right, the source of each next symbol has already been
decoded.

For the recurrence, an optimal cover of the first \(t\) positions either
leaves position \(t-1\) literal, giving \(D(t-1)\), or ends with a unique
command \((i,s_i,\ell)\), where \(i+\ell=t\). All prior commands lie in the
first \(i\) positions and contribute at most \(D(i)\). Conversely, every
listed branch appends a legal nonoverlapping command to an optimal prefix.
Induction proves the recurrence. On ties, prefer fewer commands, then the
literal branch, then smaller start and source.

Transmit selected commands in target order and transmit uncovered symbols in
their original order. The decoder scans target positions. At a command start
it copies \(\ell\) symbols forward from the already started prefix; otherwise
it consumes one literal. Induction on target position proves exact
reconstruction.

A suffix array and LCP array take \(O(n\log n)\) time with a doubling
construction. A range-minimum structure gives \(O(\log n)\) LCP queries.
Ordered insertion gives two queries per position. With maximum command length
\(L_{\max}\), the cover DP uses \(O(nL_{\max})\) time and \(O(n)\) storage.
