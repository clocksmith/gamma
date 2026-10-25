# Minimal public dependency closure

Publish these existing helper files **unchanged**, in addition to the R4 allowlist:

-`../explicit-basis-v2/segmentation.py`: self-contained codepoint/UTF8-byte exact DPs.
-`../explicit-basis-v2/accelerator.py`: standard-library-only hash-bound ctypes
 scorer bridge; no corpus loader, candidate evaluator or registry.
-`../explicit-basis-v2/score_kernel.c`: trusted exact source-as-data trie scorer.
 The source is required to reproduce a native scorer without distributing a binary.

Their exact SHA256s/provenance are pinned in`PUBLIC-CHECKPOINT-v2.json`. No edits
were made to these dependencies. Existing historical result pins remain unchanged.
`test_kernel_dependency.py` builds this public C source into a temporary directory,
checks synthetic Unicode/tie/unreachable cases against both Python DPs, and checks
wrong-hash rejection. It executes **only the trusted scorer**, not JavaScript,
Python candidate programs, cases, models or an untrusted harness. Both focused
dependency tests pass under20CPU-seconds/512MiB; no binary is published.

The remaining external import closure is already tracked:
-`../literals.py` and`../readable-v1/literal_codec.py`, standard library only.
-`../../catalogue/known_spec_service.py`, which imports tracked`catalogue.py`,
 `retrieval.py`, `materialize.py` and`boundary_policy.py`; these in turn use the
 standard library and each other. They preserve existing authority and gates.

Do **not** add`explicit-basis-v2/measure.py`, `search.py` or their legacy tests:
those pull absent historical experiment helpers and are not imported by this
checkpoint. The new focused tests cover the actual minimal helpers directly.
No private source pool, ledger payload, kernel binary or runtime artifact is part
of the publication. Real diagnostics still require separately authorized local
artifacts and live gates; synthetic controls run without them.
