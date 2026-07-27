# Independent Problem CQQ-1: C++ Comment Quotient

Status: `FROZEN RESEARCH PROBLEM`
Version: `CQQ-1`

## Given

Let \(S\) be a finite sequence of well-formed UTF-8 C++14 translation-unit
bytes with no raw string literal. Define \(Q\) by the following finite lexical
scan outside ordinary string and character literals:

1. Replace each line comment by one space, preserve every physical newline,
   and continue the comment across each backslash-newline splice.
2. Replace each block comment by one space and preserve every newline within
   it.
3. Copy every other byte exactly.

The input supplies a fixed compiler, flags, source paths, and auxiliary files.

## Questions

1. Construct the deterministic finite-state transducer \(Q\), including
   escaped quotes, character literals, line splices, unterminated-input
   rejection, and raw-string rejection.
2. Prove that \(Q\) preserves the preprocessing-token sequence and every
   physical line number at which a retained token occurs.
3. Deduce equal preprocessing and compilation for programs whose observable
   translation does not depend on comment spelling or removed columns.
4. Give a finite instance verifier that rebuilds both source sets and compares
   complete output bytes and ELI-1 loader projections.
5. If the rebuilt executable is byte-identical and the package shrinks from
   \(P\) to \(P'\), prove that the conditional score delta is exactly \(P'-P\).
6. Explain why native wrapper, resource, and full-corpus receipts remain
   mandatory.

## Frozen enwiki9 transfer

Apply \(Q\) to every `.cpp` and `.h` member in the canonical B2 SCC-1 closure,
preserving paths and all other members. The only accepted construction is the
one emitted by `tools/cpp_comment_quotient.py`. Promotion requires two
byte-identical clean builds equal to B2 and the same native 250K gate as SCC-1.
No lexer, whitespace, or coder ladder is permitted.
