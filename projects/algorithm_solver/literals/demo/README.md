# Binary literal composition in 256.one

Status: implemented and locally verified. Open the demo's **Workspace → Shared7 development validation and replay** panel. It coexists with the four main BITS input modes and typed composition. This is human binary assembly and offline reconstruction, not autonomous
selection from a problem description or evidence for 3b.

## Frozen language and input protocol

The [dictionary and 20 guides](literal-language.json) preserve every ID and UTF-8
string from [shared7](../pass2/working/README.md), introduced at Gamma commit
`0951af88c332818133f132cce9d6cf8e277b90cb`. The counted LTD1 dictionary SHA256 is
`62ab89348d4781187375f35663f81b6304a70b9f951d9bd3327fecae6d3b8c39`.
It contains 79 literals and occupies 3,507 bytes. No source, helper, wrapper,
identifier, separator or constant is inserted outside concatenated literals.

The new interactive protocol is `gamma.literal-shared7-interactive.v1`:

| Seven-bit value | Effect |
|---|---|
| 0–78 | Append exactly that frozen string |
| 79–124 | Deterministic unused-ID error; undo input to correct it |
| 125 / `1111101` | Undo the last retained literal |
| 126 / `1111110` | Reset retained source; keep the attempt's bit history |
| 127 / `1111111` | Finish a nonempty program |

Controls are protocol words, not new dictionary entries. Finish costs seven
additional bits per program. The frozen 154 selections / 1,078 source bits are
unchanged; twenty clean finished interactive streams use 1,218 bits, excluding
JSON recording overhead. Undo/reset histories cost their actual entered bits.
The UI separately shows literal, control, rejected, partial and total stream
bits, retained-source bits, all entered bits and Undo-bit actions. Undo-bit and
New-attempt are explicit administrative actions, not free source edits. A
problem guide displays IDs/bits but never inserts them.

Input is bounded to 8,190 retained bits, 16,384 input events and 64 KiB source.
Export/import use the same 1 MiB record limit. Session JSON contains dictionary
identity, events, bitstream, selections, source SHA256, cost accounting and test
receipts. Replay recomputes and checks these fields, then becomes read-only.
Imported test receipts are historical, unsigned records, not revalidated proof.
Attempts are local; export before closing the page to retain them.

## Execution boundary

The page never evaluates assembled JavaScript. Pair the existing Gamma bridge
using its unchanged Connect flow, finish the bitstream, then request validation.
The `literal_check` operation in [literal_editor.py](../../algsolve/literal_editor.py)
accepts only the fixed profile, dictionary hash, one of the twenty problem IDs,
and the binary stream. It decodes again and checks outputs and input preservation
using the pinned development cases. Expected outputs stay outside execution.
The existing Linux sandbox runs Node with 3 CPU seconds, 8 wall seconds, 1 GiB
memory and a 4 MiB output limit per batch of at most 256 cases. No browser-page
eval, new authentication policy, protected cases or recognition defaults.

## Evidence and reproduction

- [Full native qualification](evidence/qualification.json): 20 programs,
  3,834/3,834 checks, plus rejected invalid source. This is a new execution run
  through `literal_check`, not a reused source-hash claim.
- [Current browser receipt](evidence/current-browser-receipt.json): desktop 1280×900 and mobile
  390×844; real pairing and sandbox validation for #242 (264 cases) and #594
  (157 cases); unused ID, Undo-bit, Undo-literal, Reset, Finish, export and
  read-only replay; no page errors, failed lab requests or horizontal overflow.
- [Desktop recording](evidence/current-desktop-session.json) and
  [mobile recording](evidence/current-mobile-session.json) replay exact tested streams.
- Existing [semantic codec](evidence/semantic-codec-regression.json),
  [semantic editor](evidence/semantic-editor-regression.json), and
  [macro input](evidence/composition-input-regression.json) regressions passed.

From `projects/algorithm_solver`:

```sh
node literals/demo/test-literal-input.mjs
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s tests -p test_literal_editor.py -v
# Requires the existing qualified Linux sandbox and Node; writes a new receipt.
python3 literals/demo/qualify.py /tmp/literal-qualification.json
PYTHONPATH=. python3 -m algsolve.composition_bridge --port 8875
```

Serve the 256one `public/` directory on localhost:8874. With an already installed
Playwright and Chromium, set `PLAYWRIGHT_MODULE`, `CHROMIUM_PATH`, and
`LITERAL_TEST_OUTPUT` to an existing output directory, then run
`node literals/demo/browser-smoke.cjs`. `LITERAL_DEMO_URL` optionally overrides
the local URL. The smoke test uses the bridge's existing local pairing UI.
No dependencies or models are downloaded by these commands.

## Site integration and provenance

The four `literal-*` assets here are byte-identical to the seven-file deployment
overlay. [Panel markup](panel.html), [current wiring patch](256one-live-wiring.patch)
and [overlay hashes](deployment-overlay.json) target Hosting version
`d7262c3089ad6dbf`. Preserve every other live path and Hosting configuration;
recheck the release before publication. The patch uses zero-context unified
format (`git apply --unidiff-zero`); verify base hashes first. The original
[local wiring candidate](256one-wiring.patch) targets 256one Git base
`1f647ebf12e9dd06a3d0244a5a51a4e78dc32b6e` and is not a complete deployment tree.

A concurrent release activated the main BITS literal mode. This validation
section is collapsed by default and has exclusively `gamma`-prefixed DOM IDs.
The main `bits-literal-shared7-v1` profile uses command IDs 79–81; this validation
protocol uses 125–127. Records are not interchangeable. The 79 source strings
are identical. The panel never changes the main editor's source.

The current smoke check preserves all four main encodings, switches into and out
of native literal mode, and retains typed composition and the explorer link.
Set `LITERAL_EXPECT_EXPLORER=1` for this check. Earlier local/live-layout receipts
remain in `evidence/` as history. An initial preview lacked shared CSS imports;
those were restored before final visual checks. Two deployment guards stopped
before creating any version when concurrent releases changed the target files.

`export-language.py` deterministically rebuilds the readable JSON from frozen
shared7 inputs. No existing package is overwritten. Git history identifies the
introducing integration and compatibility commits; qualification records pin
runtime/dictionary/source hashes. Deployment receipts separately establish live
state. Offline encoding and human input do not establish autonomous assembly.
