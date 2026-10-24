# Amendment 1, 2026-10-24: start-dictionary hash, H3 on failure, docstring (before launch)

Nothing has launched. A fresh-context Claude subagent reviewed the freeze `9296d383f`, standing in for codex, who is out
until 2026-10-30. It found no blocker.

1. **The start-dictionary hash (found by the disclosed smoke, missed by the review).** The report hashed the start
   dictionary with a literal backslash-n instead of a newline. That came from an escaping slip, at run.py
   `start_dictionary_sha256`. repair43's start hash was therefore `4927ed1b…`, not the seed's `6a4972f6…`, and
   evidence.py's identity check would have failed after the run. It now hashes `json.dumps(...) + '\n'`. That is
   item 77's byte format, and it reproduces `6a4972f6…`.
2. **H3** is now False, not None, when a repair arm fails. The FREEZE reads "both repair arms accept", so a failure
   makes it false. H5 records the failure as well.
3. **The capped.py module docstring** no longer says solve() is unchanged.

The 9 tests pass. The smoke is re-run after this change, and the stand-in follows it. No arm, budget, rule or other
prediction changes. This file is added to the contract.
