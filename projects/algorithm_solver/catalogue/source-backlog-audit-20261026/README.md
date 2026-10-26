# Source backlog reconciliation, 2026-10-26

This is a dated evidence snapshot. [The milestone registry](../MILESTONES.md)
remains the current status owner. Source availability, catalogue metadata,
independent qualification and permission to execute remain separate.

## Checked against the actual sources

[RECONCILIATION.json](RECONCILIATION.json) binds the input hashes, the inspected
Git revision and the private Jupiter catalogue's SHA-256. The supplied audit's
3,052 published patch-source Git identities match main, including its corrected
blob identities; the two absent batches still have no files at their recorded
paths. No source file was replaced and no algorithm or protected case was run.

The Jupiter catalogue was read over SSH as metadata. It contains 4,081 problem
records, with 943 marked qualified in each language and the same 943 paired IDs.
This verifies the count and snapshot identity; it does not independently verify
those qualification claims, their receipts or the source files they reference.
The raw private catalogue and its per-ID protection/status membership are not
published here.

The supplied census records both-language source evidence for 1,918 IDs. Of the
943 paired catalogue records, 937 overlap those IDs and six add metadata
references outside that census. The remaining 2,157 IDs are **not located in these
supplied references**, not proven unwritten. The global missing-implementation
count remains unknown. Metadata status and source-hash matches are reported
separately in the reconciliation JSON.

## Still needed for patch integration

The downloads contain the three audit documents below, not these source payloads:

- `gamma-64-more-medium-solutions-v2.patch`: 64 pairs / 128 source files.
- `gamma-hard64-v2.patch`: 64 pairs / 128 source files.

Their intended batch directories are absent from the inspected Git tree, and
none of the 256 recorded pending source blobs exists in the local Git object
store. The report's referenced ZIP, `pending-patches/` and
`reconcile_local_inventory.py` were not supplied. The original candidate bytes
are needed before importing those batches; inventing replacements would not
apply the reported patches. Existing corrected implementations stay intact.

## Preserved inputs

- [REPORT.md](REPORT.md): original supplied source audit, with its original scope
  and observation dates. Its earlier unverified Jupiter statement is superseded
  only for the metadata count and snapshot identity by the reconciliation above.
- [already-written-patch-only.md](already-written-patch-only.md): reported pending
  integration candidates, not new implementation assignments.
- [source-inventory-4081.json](source-inventory-4081.json): source-reference census;
  not a canonical qualification catalogue or an authorization list.

All three input files are preserved byte-for-byte. No gates, historical verdicts,
protected-data permissions or scientific qualification statuses are changed.
