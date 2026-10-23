# Pre-launch loader correction, 2026-10-23

The freeze requires non-ASCII source to remain unchanged. Before any run,
reviewing the loader found `decode('ascii')` would instead abort before the
rewrite policy could preserve it. Decode UTF-8 and keep the existing no-rename
guard; an unencodable validation program is retained as a coverage failure.
Fix entry-body extraction to respect AST UTF-8 byte positions too.

One added synthetic Unicode body-span check passes (11 tests total). No corpus
measurement, source selection, partition, search budget, prediction or readiness
rule changed. The 27 fit sources audited before the freeze were all ASCII.
Updated code hashes and this note are pushed before launch and sent for review.
