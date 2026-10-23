# Prelaunch amendment1: Python newline offsets

2026-10-23, before any corpus run. Claude review of fe5ed5ba4 found that
str.splitlines also treats vertical tab, form feed and several ASCII record
separators as newlines. Python does not treat these as source line boundaries
inside comments, so AST line/column offsets could address the wrong Name span
and abort an arm. Both graph extraction and structural validation now compute
line starts using only CRLF, CR and LF, matching Python source newlines.
An unexpected span assertion during graph extraction retains the original as
unsupported(scope_mapping_assert), with its reason in the ordinary trace.

One regression test checks all15 combinations of the five comment control
characters with LF/CR/CRLF, verifies exact local spans and structural validation,
and executes original/renamed programs for matching outputs. The existing28tests
remain. No corpus probe or candidate cost informed this fix. Population, search,
source policy, budgets, promotion and charging stay unchanged. The contract pins
this amendment and changed graph/test bytes; the original FREEZE remains intact.
