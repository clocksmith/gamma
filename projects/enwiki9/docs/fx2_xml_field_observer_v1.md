# Native XML field observer, synthetic stage

Owner: `root_explore`. Component identity: `fx2_xml_field_observer_v1`.
This is implemented observer work, not a queued corpus comparison. Source,
ownership and a frozen native gate must publish before corpus execution.

The standalone field repair saved 301, 71 and 1,541 archive bytes on its
[development](../operations/provenance/opcode_field_repair_terminal_20260908.json),
[validation](../operations/provenance/opcode_field_validation_terminal_20260908.json)
and [confirmation](../operations/provenance/opcode_field_confirmation_terminal_20260908.json)
populations. Its compact delivery remains unpaid under the conditional doubled
source-ZIP comparison. Those gains do not transfer to FX2. The matched frontier
comparison ran unchanged FX2, and no native field-transfer result is established.

Discovery lenses 6 and 9 were chosen deliberately: test a missing coordinate
against equal-capacity controls. Lens 3's history-bank direction was replaced:
field-history validation lost to its randomized control, and Fiber/LOOM work has
existing exclusions or ownership. Another final calibration sweep and a rescue
of the losing BPD1 dictionary representation are unselected.

FXCM already recognizes text, nowiki, math and pre boundaries and has generic
HTML, bracket and template contexts. Source review found no explicit coordinate
for the six exact fields below. This is a modeling hypothesis, not an assertion
that FX2 contains the standalone recognizer's bug.

The [native component](../lib/fx2_xml_field_observer_v1.hpp) consumes one modeled
WRT text segment: initial flag 7 followed by code events. It implements the
retained WRT inverse's byte involution, one/two/three-byte dictionary codes,
case flags and escaped literals. A word becomes visible only after its complete
codeword. Emitted raw bytes update a bounded exact suffix recognizer:

| Coordinate | Completed opening spelling | Closing spelling resets to zero |
| --- | --- | --- |
| 1 | `<title>` | `</title>` |
| 2 | `<id>` | `</id>` |
| 3 | `<timestamp>` | `</timestamp>` |
| 4 | `<username>` | `</username>` |
| 5 | `<comment>` | `</comment>` |
| 6 | `<text xml:space="preserve">` | `</text>` |

Recognition does not normalize spelling, expand entities or validate XML.
Unrecognized/malformed markup remains raw bytes. Any recognized closing marker
sets zero, matching the standalone rule; there is no inferred nesting stack.
State serialization includes the complete marker tail, partial codeword, case
flags, counters, limits, failure and finish flags in 66 bytes. Bind the immutable
dictionary and source separately; serialization is a hash input, not a restore
API or a claim that the dictionary is free.

The constructor copies its supplied dictionary before checking limits. Its
allocation bound therefore assumes an already bounded caller-owned dictionary;
native integration must validate the pinned input before construction. The
component is not an arbitrary untrusted-dictionary loader.

Seven [synthetic tests](../tests/test_fx2_xml_field_observer_v1.py) pass with
optimized and UBSan builds in the [unit receipt](../results/fx2_xml_field_observer_v1_unit/attempt02/receipt.json).
They compare event emissions to the retained Python WRT inverse, verify raw
field states and deterministic serialized repeats, and exercise incomplete
tokens, malformed references, escapes, simultaneous case flags, raw limits,
failed-state handling and incomplete markers. The failed first attempt remains
retained: the suffix buffer omitted the longest marker and one synthetic high
byte lacked its WRT escape. These were implementation/fixture errors, not
compression results. CPU3, 512MiB address space, 64MiB scratch, 30 CPU seconds
and 45 elapsed seconds per phase, 180 seconds aggregate; no corpus/model run.
Independent review rehashed all five source and eleven artifact bindings and
checked the actual decompressed opcode table and WRT inverse. It found no
blocking logic defect. Remaining boundary fixtures for integration include a
short dictionary's token overflow, a zero-output control stream at the work
ceiling, and a word expansion exceeding the remaining raw limit.

The next native mutation changes only the first nonstationary `{0}` word model's
context to `words_[0] ^ (field * 0x9e3779b97f4a7c15)`. Use a dedicated scalar:
the original Sparse context is shared with a match model. Preserve construction
order, random calls, model capacity and update mechanics. Refresh the scalar
after existing context updates and completed WRT observation, before ByteUpdate.
During dictionary pretraining, update the scalar with field zero and suppress
the observer; reset only observer state at the true modeled segment boundary.

P stays original. K/G run observer machinery with effective field zero and must
match P. D uses the current field. S uses the field delayed by 4,096 completed
modeled bytes; allocate/update the same ring in K/D/S. This is temporal
displacement, not label renaming. Record D/S disagreements and their contingency
table; inadequate separation does not authorize choosing another delay.

Before opening250KB, implement the source adapter, synthetic native call-order
checks and frozen runner. Bind one fixed context law, raw/WRT identities, source,
dictionary/model, arm/package costs, resource stops and all-state witnesses.
Require exact inverses, independent repeats, P/K identity and D beating P/G/S.
Only a controlled package-paying result justifies fresh confirmation. Shared-map
collisions may propagate D's changes; require within-arm encoder/decoder state
agreement, not D/P equality. Full score and complete package remain unknown.
