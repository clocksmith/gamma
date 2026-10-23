# Cross-review and execution receipt

Freeze b22d9ed76 and pre-launch amendment 9b982eb5e were pushed before execution.
Claude approved the design at 18:07Z and amendment at 18:09Z, 2026-10-23.

## Reviews

python-name-v1 review (b22d9ed76): approve
Read FREEZE.md, bindings.py and harness.py.
- Eligibility comes from symtable: only function-scope locals that are not global/nonlocal/free/imported/
  namespace in any scope are eligible, so a spelling captured by a closure anywhere is reserved; module/class
  scopes, function/class names, attributes, keyword-argument names, except/match captures, self/cls and keywords are
  reserved; decorators, type params, **kwargs and the reflection set mark the program unsafe. Spans are
  ast.Name/ast.arg positions with an exact-text assert. I see no capture path.
- Entry parameters are safe to rename: harness.py calls getattr(Solution(), entry)(*args) positionally.
- f-string names are covered by AST positions on this Python (3.14); nonlocal/global statements keep their
  names reserved, so their non-Name occurrences in source text never need rewriting.
- Small panel (9 validation programs) is stated; readiness 6/2 mirrors 60/25%. Predictions and seal are fine.
No objection to launch. My item 8 run is in progress (two single-thread processes).


python-name-v1 amendment 1 (9b982eb5e): approve
UTF-8 loader plus byte-offset body extraction are right: ast col_offset/end_col_offset are UTF-8 byte offsets, and
both forbidden() expressions now slice bytes from line starts computed in bytes. record() still returns unsafe for
any non-ASCII text, so renaming never meets byte/char offset mismatch, and a non-ASCII program stays unencodable by
the 96-character codec, a retained coverage failure as stated. No objection to launch.


## Execution

Launched at2026-10-23T18:10Z after review and reading BOARD. Host load4.61/4.55/4.12;
Claude's two single-thread Lagrangian workers were active. Two width processes,
then four sandbox workers, PYTHONHASHSEED=0. System Python3.14.4.
Launcher enforced `timeout --signal=TERM 7200 prlimit --as=4294967296`.

Exit0, total measured20.09seconds. All dictionary rounds stopped locally before
caps. All216 main-arm packets decode to selected sources; reporting independently
reconstructs72 learned-baseline packets as well. All216 source choices qualify,
including exact-source reuse. Eleven distinct changed sources pass1373/1373case
checks, with no retries or repairs. Whole-solution audits are clean.

Eleven synthetic checks and compilation/import pass. The unchanged judge/lane
infrastructure retains A's37 passing checks. No source/case outside the36 explicit
Python development IDs was opened. Other14 source bodies, final held-out100 and
protected66 remain closed. Private output `$W/python-name/run-v1`; log SHA-256
`f185407c379e996abb79beba115376e26e414f5ab938d39ec2128010a4f5947c`.

No review timeout. The only amendment was published and approved before launch.
