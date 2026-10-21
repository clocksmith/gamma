# Qualified JavaScript and Python guidance packages

This release contains exact, qualified development solutions for **150 JavaScript problems** (79 Easy, 54 Medium, 17 Hard) and **50 Python problems** (10 Easy, 30 Medium, 10 Hard). Matched 128-entry/7-bit and 256-entry/8-bit profiles preserve their ordered concrete strings and explicit sequences. A Python 256 storage alternative is also retained. These are offline encodings of supplied programs, not autonomous synthesis or M1 qualification.

## Guide-export measurements

| Profile | Problems | Entries / bits | Selections | Median / p95 / worst | Character selections | Dictionary + packet bytes |
|---|---:|---:|---:|---:|---:|---:|
| js150-128-guide-v1 | 150 | 128 / 7 | 19,979 | 119.5 / 292 / 431 | 15,722 | 1,676 + 23,702 = 25,378 |
| js150-256-guide-v1 | 150 | 256 / 8 | 12,313 | 70.5 / 201 / 305 | 7,143 | 3,929 + 18,463 = 22,392 |
| py50-marginal-128-guide-v1 | 50 | 128 / 7 | 8,624 | 154.0 / 305 / 347 | 5,934 | 953 + 9,617 = 10,570 |
| py50-marginal-256-guide-v1 | 50 | 256 / 8 | 4,675 | 81.5 / 187 / 197 | 1,994 | 2,155 + 6,725 = 8,880 |
| py50-frequency-256-guide-v1 | 50 | 256 / 8 | 4,679 | 82.0 / 187 / 197 | 1,991 | 2,141 + 6,729 = 8,870 |

The per-profile `metrics.json` files are authoritative, including selection bits, character fraction, padding and framing. Each packet includes 41 framing bytes. Dictionary costs charge the full UTF-8 strings and framing. Every emitted source byte, helper, wrapper, identifier and import is present in the reconstructed source. There are zero whole-solution dictionary entries. UI control actions, navigation/correction costs and interpreter distribution are not included in these payload measurements.

The JavaScript guide export deliberately differs from its research winner. For problems 62 and 64 in the 7-bit profile and 64 in the 8-bit profile, it uses exact previously public qualified compact sources, parsed optimally under the unchanged current dictionary. This avoids distributing other source variants outside this release's reviewed scope. The substitutions add 91 selections to the 7-bit research total (19,888→19,979) and 19 to the 8-bit total (12,294→12,313). Their source hashes, public provenance and before/after costs are recorded in [provenance.json](provenance.json). Original research receipts and winner measurements are unchanged. This guide export is not a new research improvement claim.

## Assets and identity

[guide-assets.json](guide-assets.json) contains five immutable profile identities, ordered dictionary strings, exact source and sequences, canonical problem metadata, binding signatures, recorded qualification and sample-context availability. Source files are deduplicated by problem/hash under `sources/`. Every profile has `dictionary.json`, `dictionary.bin`, `programs.json`, `metrics.json` and its independently verifiable packets in `profiles/`.

The input-cost choices are `js150-256-guide-v1` and `py50-marginal-256-guide-v1`. The Python frequency profile uses four more selections but ten fewer package bytes; retain that storage tradeoff separately. Existing BITS shared7 remains a distinct pinned profile. Never reinterpret its IDs through these dictionaries. Full 128/256 dictionaries have no unused IDs for undo/reset/submit: UI controls require an explicitly versioned, separately counted protocol.

All selected sources have passing recorded source-version qualification. [qualification-receipts.json](qualification-receipts.json) publishes per-source finite check counts and original receipt hashes, without raw test cases or private execution paths. No new native execution or source qualification was performed for this export. The independent verifier decodes 450 packets, checks minimum parse lengths with a forward shortest-path oracle, validates source/packet/dictionary hashes and all accounting, checks 188 unique JavaScript and 51 unique Python sources syntactically, and verifies notice hashes. Syntax checking does not execute source or replace semantic qualification.

Run `python3 verify.py` with Python3 and Node available to reproduce the package checks. [verification.json](verification.json) records the preparation-time outcome. A local rerun writes `verification-rerun.json`.

## BITS integration boundaries

JavaScript150 includes the existing 20 public BITS sample contexts; 130 lack a bundled browser sample context. The Python50 panel has no matching context in that existing public 20 set, and JavaScript execution support does not supply a Python runtime. Every guide carries its entry/interface/positional binding metadata. Integrations must verify runner adapters against actual public fixtures; show an explicit unavailable/unsupported result where fixtures or runtime are absent. Guidance availability and sample execution availability are separate capabilities. No raw research cases, automatic execution or remote runner is introduced by this package.

ASCII guidance can use the exact selected source bytes where the character alphabet permits them. Python indentation and imports must be emitted explicitly. An interface must not inject helper code, rename parameters invisibly or treat stored sequences as evidence of autonomous composition.

## Provenance, permissions and limitations

The prior public 80 JavaScript IDs overlap the 150 panel exactly; 70 additional JavaScript IDs and 50 Python IDs are included under the new source/dictionary/sequence publication approval. JavaScript dictionaries contain fragments learned across all 150 programs. The public guide sources for overlapping IDs were verified against existing public history, with the three substitutions described above. No private Git ancestry, raw dataset, credentials or raw evaluation cases are included.

Canonical difficulty uses pinned doocs metadata revision `88c8c2c29f19c186d7cc05c9db17245d9ae3df43`; JavaScript labels were also corroborated against newfacade revision `215604aeed660029df7de2fea5a4d7b6ed476a08`. Exact metadata receipt hashes are in [provenance.json](provenance.json). Difficulty is snapshot metadata, not inferred from program size.

Retain [NOTICE.txt](notices/NOTICE.txt), [license metadata](notices/UPSTREAM-LICENSE-METADATA.json) and all accompanying license/notice texts. The recorded Hugging Face dataset card says Apache-2.0 while the captured linked GitHub notice says MIT. This release preserves both and does not invent a new license grant or treat those terms as interchangeable. Owner-supplied normalized candidates and reference attribution must remain distinct; referencing a dataset does not assert every candidate was copied from it. The doocs notice is retained as reported metadata without asserting applicability to every source. Existing finite qualification does not prove arbitrary-input correctness, maximum-bound complexity, untouched generalization or publication novelty. M1 remains unmet.
