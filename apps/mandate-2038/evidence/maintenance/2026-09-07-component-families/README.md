# Three physical component families

The selected forms are cards (including flat chips), Agent position tokens,
and cubes. Five track cubes per faction replace captive sliders. Facilities,
Generators, matched project pairs, Fusion, Current Era, and Initiative use flat
chips. Mandate uses a score-track cube. Audit cubes retain their individual
supplies and tactile requirements; numerical track cubes never enter the bag.

All three project references stay face up. Mega-Cluster and Fusion chips use
Available/Built faces; current connections determine whether a built project
operates. Quantum keeps the existing personal checkbox. Trust awards retain
permanent checkboxes. Shared references are not completion records, and Facility
and Generator must not share opposite faces of one piece.

The physical specification, setup, inventory, source supply record, generated
rulebook and reference copy agree. The stale two-reference setup and board count
were corrected to three. The earlier manufacturing study is explicitly retained
as historical quote assumptions. Project prices, benefits, Era unlocks, ownership
and completion limits, and Audit probabilities are unchanged. A structural
comparison of components/game.json and components/projects.json against the base
commit found only the slider-to-track-cube supply field and Fusion chip wording.
No runtime algorithm, lore, or browser interaction was changed.

## Verification

Executable 0.19.16, physical candidate 0.11.0-rc.18-test, engine 0.22.5.
All 312 tests pass with no failures or skips; eight focused authoring checks also
pass. Build, content checks, immutable release verification, local public package,
and diff whitespace checks pass. The rulebook is 6,478 words against its unchanged
6,500-word limit. All 1,386 captured source files matched after the test run.

Earlier failures are retained: 310/312 passed before tightening the expanded
rulebook and correcting the Mandate cube assertion; 311/312 passed before replacing
an opening-sentence assertion with a check that the complete authored inventory
appears in the rulebook. No limit or gameplay assertion was weakened. Both rejected
source captures and logs remain here; earlier immutable releases remain intact.

These are specification and software checks, not manufactured chips, printer-ready
dielines, physical handling evidence, human learning, or balance results. Nothing
was pushed or deployed for this update.
