# Solution to CQQ-1: C++ Comment Quotient

Status: complete constructive solution
Version: `CQQ-1-SOLUTION`

Use states `NORMAL`, `STRING`, `CHARACTER`, `LINE_COMMENT`, and
`BLOCK_COMMENT`, plus one escape bit in the two literal states. In `NORMAL`,
the pairs `//` and `/*` enter their comment states after emitting one space.
Quotes enter their corresponding literal state and are copied. Literal bytes
are copied until an unescaped matching quote. A line-comment newline is copied
and normally returns to `NORMAL`; a backslash-newline is copied as a newline
while remaining in `LINE_COMMENT`. Block comments copy only newlines and exit
at the first `*/`. End of input in a literal or block comment is rejected.
Encountering a raw-string introducer is rejected by hypothesis enforcement.

C++ translation phase three replaces each comment by one space after
backslash-newline splicing. The transducer emits exactly that separator while
retaining the same noncomment bytes. Preserving all physical newlines keeps
every retained token on its original physical line. The special line-splice
case removes all bytes belonging to the continued comment while retaining the
same count of physical newlines. Therefore the preprocessing-token sequence,
directive boundaries, literal contents, and retained-token line numbers agree.

Under the stated exclusion of comment-spelling and removed-column
introspection, equal preprocessing tokens and fixed compiler inputs give equal
translation semantics. The finite instance verifier is stronger: it rebuilds
both closures twice, hashes complete binaries, and compares ELI projections.
Byte identity implies projection identity immediately.

For common archive length \(A\), parent and quotient scores are \(A+P\) and
\(A+P'\). Their exact conditional difference is \(P'-P\). The proof does not
execute the wrapper or bound compilation, compression, decompression, memory,
or full-corpus score, so those remain measured obligations.
