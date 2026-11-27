# Frozen JavaScript transfer cohort

The sampling unit is a public upstream GitHub repository. Each selected owner contributes one repository. The measurement population is every tracked, regular, case-sensitive `.js` file at the pinned default-branch commit, including examples, tests and distribution files. Symlinks and submodule references are different Git object types. The cohort measures transfer to small MIT-licensed repositories in the frozen GitHub search frame.

## Selection before source access

1. Freeze the repository metadata from pages 3 through 5 of the GitHub repository search in `candidate_frame.json`. The order is descending by stars with 100 rows per page. Treat the saved frame as authoritative because search results can change. See `discarded_frame.json` for the exclusion of an earlier preliminary search and all its owners.
2. Rank each repository by SHA-256 of UTF-8 `bits/frozen-js-transfer/v1`, one zero byte, then the case-folded GitHub owner/repository name. Reject duplicate GitHub IDs and matches to published historical owner, repository and protected-domain tokens. Domain screening uses the repository name, description and topics. The A1b public calibration metadata identifies the 59 capacity corpora, upstream aliases, previous fit owners, 14 calibration owners, and five reserved domain families. Public objective and closure manifests supply additional spent file hashes. The primary fit and spent CodeNet, Express, Ramda and algorithm collections are covered by the historical registry. The index is reconstructed from those public records and the custodian's hash-only export.
3. Resolve the first 100 remaining candidates. A GraphQL query requests only the default branch name, commit OID and root tree OID. The recursive Git tree API returns file paths, object IDs, sizes and modes. Reject truncated trees. A repository qualifies on metadata when it has 1–25 tracked regular `.js` files, 256–16,000 total JS bytes and 1–8,192 bytes in each JS file. Store the entire eligible file list, including upstream blob IDs, before fetching any candidate blobs.
4. Traverse the fixed eligible order. Verify every fetched blob using its declared length and the Git SHA-1 object ID. Reject an entire repository if any file duplicates a historical fingerprint, previously selected file or sibling file. Record the rejected file and duplicate type. Keep the first 20 passing repositories from distinct GitHub owner IDs. A squeezed fingerprint is SHA-256 of the bytes concatenated after Python `bytes.split()` without explicit separators. Content is used only to verify identity and reject duplicates.

The custodian supplied 4,392 distinct historical squeezed hashes from the original primary, A1b historical development and 14 calibration organizations, and both A2 splits. The opaque list is pinned by SHA-256 in the sampler. Public historical manifests also provide exact hashes. A match against a historical squeezed fingerprint catches both byte-for-byte and whitespace-only duplicates. Private or unpublished protected fingerprints cannot support a content-level disjointness claim. Protected domains and spent upstream identities were screened using their available metadata. The upstream programs were treated as opaque bytes throughout.

## Replay

Run the commands from this directory. The checked-in frame and pins are immutable. Materialization reads those pins directly and retrieves missing blobs by Git object ID. It uses the authenticated GitHub CLI and Python's standard library.

```sh
python3 freeze_cohort.py materialize --cache /tmp/bits-frozen-js-v1
```

`source_manifest.json` records source paths relative to the cache's `corpus/` directory, lineage IDs, sizes, Git blob IDs and raw and squeezed SHA-256. `cohort_audit.json` records the selection-pin digest, source-manifest digest, exclusions during ranked traversal and overlap counts. Source bytes stay outside Git.
