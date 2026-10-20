# Binary literal composition in 256.one

Status: implemented and locally verified. Open the demo's **Workspace → Literal
composition** panel. It coexists with the existing typed macro and semantic
modes. This is human binary assembly and offline reconstruction, not autonomous
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
- [Browser receipt](evidence/browser-receipt.json): desktop 1280×900 and mobile
  390×844; real pairing and sandbox validation for #242 (264 cases) and #594
  (157 cases); unused ID, Undo-bit, Undo-literal, Reset, Finish, export and
  read-only replay; no page errors, failed lab requests or horizontal overflow.
- [Desktop recording](evidence/desktop-session.json) and
  [mobile recording](evidence/mobile-session.json) replay exact tested streams.
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

The four `literal-*` assets in this directory are byte-identical to the served
256one assets. [Panel markup](panel.html) and [wiring patch](256one-wiring.patch)
show the scoped integration against 256one base
`1f647ebf12e9dd06a3d0244a5a51a4e78dc32b6e`. Apply only after reviewing any newer
site changes. `export-language.py` deterministically rebuilds the readable JSON
from frozen shared7 inputs. No existing package is overwritten.

This integration's introducing commit is the Git history entry for this file;
qualification records pin source/dictionary hashes. Deployment is a separate
operation and local checks alone do not establish what is live.

## Reconciled live-site overlay

The deployment preflight found a newer BITS site with static problem loading,
a composition-set explorer and retained literal-profile assets. The old local
checkout is not a complete deployment source. The [live wiring patch](256one-live-wiring.patch)
and [overlay hashes](deployment-overlay.json) target Hosting version
`05593c3b04669d47`; all other paths/configuration must be preserved.
The [reconciled browser receipt](evidence/live-browser-receipt.json) supersedes
the older-layout smoke receipt for deployment. It retains the three main input
encodings, typed composition and explorer link. The initial preview lacked four
shared CSS imports; they were restored before the final visual checks.

Existing BITS literal assets use a different input/recording protocol. This
Gamma panel explicitly uses `gamma.literal-shared7-interactive.v1`; its control
IDs 125–127 and exported records must not be mixed with that other profile.
The frozen 79 dictionary entries themselves are identical. Set
`LITERAL_EXPECT_EXPLORER=1` for the current live-layout browser smoke, or
`LITERAL_EXPECT_SEMANTIC=1` for the preserved earlier local-layout candidate.
The semantic panel's absence from the newer live base predates this overlay;
this patch neither removes nor restores it.

The wiring files use zero-context unified patches (`git apply --unidiff-zero`);
verify the recorded base hashes before applying them.
