# Readable literals — Goal 3a pilot

This is a small exact-text family within Goal 3a, not a new numbered goal or a replacement for structured constructors. It uses complete formatted lines and complete small statements/blocks containing their actual names, constants, punctuation and indentation. Some complete lines open a block and therefore do not independently balance braces; complete block entries include both ends. Typed holes, variable substitution and implicit indentation are absent.

Three admitted, previously exposed Medium development problems are represented in both JavaScript and Python: Number of Provinces (#547), Keys and Rooms (#841), and Shortest Path in Binary Matrix (#1091). Every decoded byte equals the source checked in the isolated predecessor/differential qualification: 434 decoded cases, 434 predecessor cases, 434 matches and 12 effect controls. Seven public samples per language are included; private original tests are excluded. No new corpus admissions, autonomous assembly, untouched evaluation or M1 pass is claimed.

## Guide candidates

| Profile | Entries / width | Total selections | Median / worst | Dictionary + packets |
|---|---:|---:|---:|---:|
| JavaScript readable small statements | 63 / 6 | 81 | 27 / 32 | 3,090 B |
| Python readable small statements | 53 / 6 | 57 | 18 / 22 | 3,107 B |

These are additional versioned profiles for the existing JavaScript-composition and Python-composition modes. They are not defaults and add no fourth input mode. `profiles.json` pins dictionaries, manifests and sources; each manifest contains exact selection IDs and counted bits. The preserved older profiles must not be overwritten. This package has not itself been deployed.

## What the comparison showed

The original bounded search also allowed complete native statement blocks up to 12 lines. It reached 57 JavaScript and 37 Python selections, but its largest task-specific entries occupy 38.7–48.4% of each JavaScript source and 45.5–63.0% of each Python source. Each such block supports one problem; Python #547 contains the traversal core in one entry. Those are diagnostic results, not a shared-best vocabulary or reusable whole-algorithm abstraction. Their dictionaries are not exported as guide candidates.

The stricter exported profiles permit blocks of at most three lines. Largest selected pieces occupy 9.8–12.7% of JavaScript sources and 10.0–25.2% of Python sources. Most reuse remains formatting/wrappers: seven reused JavaScript entries and two Python entries. Requiring multi-line blocks to occur in at least two different problems gives exactly the line-only result (85 JavaScript, 63 Python selections). There is no demonstrated cross-problem algorithm-block reuse in this pool.

Both 128-entry/7-bit and 256-entry/8-bit arms were measured on identical sources and candidate pools. They selected identical dictionaries/sequences, so 7-bit wins input cost here; this is not a problem-count threshold or impossibility claim. Character controls use smaller total storage but far more selections. Dictionary UTF-8 bytes, length framing, 41-byte packet headers and padding are reported in `comparison.json`. The included frozen `literal_codec.py` decoder source is 8,240 bytes, charged once across both language profiles: the exported pair totals 6,197 B for dictionaries/packets or 14,437 B with that retained decoder source. Runtime/engine distribution is separate; that host module includes measurement helpers and is not a minimal decoder claim. The website’s JSON, duplicate source display, controls and runtime assets are not silently counted inside the compact packet total.

The learned raw controls use larger, different training populations, so same-source encoding comparison is not proof of a superior learning algorithm. The historical shared7 vocabulary is an established 79-entry / 20-problem baseline with genuine counting-helper reuse; it cannot exactly encode these graph sources without changing the dictionary or source. No missing-character escape was added.

## Reproducibility and evidence

The experiment uses a frozen finite candidate pool and exact shortest-path segmentation. Dictionary add/prune search is heuristic, with a 60 CPU-second/16-pass bound; the first sweep took 2.4743 CPU seconds and the disclosed post-result size/reuse ablations took 0.3870 seconds. An independent binary reader, forward shortest-path oracle and qualification-source hash join verified all 72 packets across 24 profiles. Source execution was not repeated for identical bytes. Attribution/provenance is retained in `ATTRIBUTION.json`; missing upstream repository refs are not invented.

Future progress requires validated shared source/helper rewrites and a broader qualified development comparison, not merely making problem-specific blocks bigger. Balanced constructors with typed holes remain a separate structured representation related to 2a/2b; readable flat literals belong to 3a/3b. Neither offline representation establishes autonomous solving.

## Six-bit encoding revision

The later explicitly frozen ≤64-entry arm keeps every dictionary ID and source byte unchanged. JavaScript uses 486 selection + 10 padding + 984 framing bits; Python uses 342 + 10 + 984 bits. Matched seven-/eight-bit payloads are JavaScript 567/648 and Python 399/456 bits. Pair dictionary+packet bytes are 6,197 (6-bit), 6,214 (7-bit) and 6,229 (8-bit). This is a width change, not a new vocabulary or a character fallback.

All six packets were decoded by separate bit extraction and checked against the qualified source hashes; 29 wrong-hash/truncated/trailing/unused-ID/padding controls were rejected. Small host codec measurements and traced allocation peaks are in `comparison.json`; they are not execution benchmarks. Source runtime/memory behavior is inherited only through exact byte identity with the qualified programs, not a new solver speedup. This export remains a proposed guide package, not a deployment receipt.

See [complete source and ID examples](EXAMPLES.md).

## Reproduce the encoding from this installed package

Run `python3 -B reproduce.py` from this directory (or pass its full path). Python 3.9 or later and the standard library are sufficient. The command reads the six included source files as bytes; it never imports or executes them. It checks the package file hashes, imports the unchanged frozen codec, repeats exact segmentation, reproduces all 18 six-/seven-/eight-bit packets, compares their preserved hashes and rejects malformed controls. To save reconstructed packet files, use `python3 -B reproduce.py --output /tmp/readable-packets-new`; the destination must not exist.

`literal_codec.py` is the exact 8,240-byte implementation whose cost and hash were reported; it has not been replaced. Its earlier direct-execution measurement entrypoint belongs to the original experiment layout, so use the packaged `reproduce.py` entrypoint here. `CODE_LICENSE.txt` preserves Gamma's MIT notice for the codec and reproduction code; it does not relicense solution/dataset material in `ATTRIBUTION.json`. `CODE_PROVENANCE.json` identifies the unchanged implementation.

The reproduction CLI, contract, license and provenance are additional review/reproduction artifacts, separately stored and counted in `FILES.json`; they are not concealed in the 8,240-byte decoder figure or compact dictionary/packet total. The full review package also retains duplicate JSON and display sources. No solver runtime or private qualification tests are bundled.
