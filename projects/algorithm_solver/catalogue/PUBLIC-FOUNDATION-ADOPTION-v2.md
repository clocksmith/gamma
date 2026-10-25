# Deliberate public-foundation adoption v2

`public_foundation_adapter_v2.py` is a separate successor, preserving the v1
adapter and all historical contracts/receipts. It replays the independently
reviewed frozen raw observations, verifies source-specific verdicts and exact
runtime/interface/tests/effects/domain bindings, and only then constructs new
normative receipts. Summary conversion alone cannot qualify a source.

The authorized 14-problem lane passed 28 source-language pairs, 3,090 cases and
110 native isolated calls. The adopted catalogue keeps **4,081 IDs /8,162 slots**
and 166 protected IDs unchanged. It now contains **400 JavaScript and392 Python
implementations;392 IDs have both**. Each language has20 normative official-domain
artifacts; the remaining380 JS/372 Python artifacts retain their explicitly
frozen-admitted scope. All784 predecessor receipts are preserved alongside28new
receipts, including replaced JS canonical receipt identities in provenance.

Eight development Python gaps remain:252,1064,1086,1087,1152,1153,1165,2898.
No protected payload access, case edits, historical failure upgrades, candidate
execution during adoption, recognition qualification or M1 claim is implied.

## Explicit scope

- Every normative artifact exposes official preconditions and frozen input
  validator identity; invoke `validate_foundation_inputs` before future query
  checking or candidate execution. V1 artifacts retain the v1 validator.
- Input preservation and fresh mutable output are separately reviewed local
  catalogue policy, not invented official requirements.
- 1514 uses official finite absolute error <=1e-5, excluding bool. Input real
  probabilities compare numerically across JSON1/1.0 spellings. Historical
  exact-comparison receipts are untouched.
- 955's **finite test oracle is partial** beyond width12 except independently
  justified equal/uniform boundary families. The full official domain validator
  is separate; no arbitrary-input oracle service is claimed. Other arbitrary
  oracle evaluations likewise require their own resource controls.
- 988 canonical trimmed BFS excludes orphans and invalid labels; separately
  pinned iterative observation handles the tested8,500-node depth.

## Verification

18 adapter/catalogue tests pass. All400 permitted exact-ID artifacts were checked,
28new frozen input gates exercised,28source locators rehashed, and all784 prior
receipts compared verbatim. The universe bytes are unchanged. Source payloads,
raw observations and mutable private serving configuration remain outside repo.

New catalogue SHA256:
`a61088b1d5a5c3cdde82b431ee7f4cdd65dd1ce0da3b625267e1d001a4dd585f`.

See `public-domain-qualification-v2/README.md` for the independent report,
review, freeze and raw-observation verification identities. Serving/CLI adoption
is a separate reviewed operation and does not imply informal recognition.
