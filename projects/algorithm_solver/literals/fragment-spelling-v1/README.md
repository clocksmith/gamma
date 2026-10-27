# Long fragments with counted spelling

Owner: [Algorithm Solver](../../CATSCAN.md), goal2a.
The owner chose long fragments plus explicit counted spelling on2026-10-27.
This protocol is separate from historical pure-literal experiments. It does not
change their source identities, M1 gates or promotion results.

## Binary contract

A primary width of6,7 or8 provides64,128 or256 codes. Code0 opens spelling;
remaining63,127 or255 codes append exact UTF-8 fragments, each at least two
Unicode characters. No renaming, substitution or source normalization occurs.
In spelling mode,1 followed by eight binary presses appends one UTF-8 byte;
0 exits spelling. Both transitions are charged. An ASCII character costs9 presses
inside a spelling run; a four-byte character costs36. One run costs the opening
width plus9 times its byte count plus one closing press.

This is a hybrid representation, not a claim that63 fragments can express every
program unaided. Report fragment bits, spelling bits and transition bits
separately. The spelled-byte contribution counts toward character costs; it
cannot disappear from the10% M1 accounting by avoiding single-character entries.
Finish, Undo and corrections must retain their separately recorded interaction
cost when this codec is integrated into BITS. No interaction has been implemented
or measured here yet.

`codec.py` finds a minimum-press exact parse with a two-state dynamic program.
The independent test oracle instead enumerates complete spelling runs. Binary
packets retain exact bit length, refuse trailing data/nonzero padding, and carry
nine header bytes. Dictionary storage includes width, count and length-prefixed
UTF-8 bytes. Cost reports must charge both files and any decoding/runtime package;
input presses are not stored bytes.

## Delivery state

The codec and seven focused tests are implemented. No fitted dictionaries,
new corpus freeze, guide publication, browser integration or human-effort result
is claimed. The larger paired corpus still needs source-specific evidence joins;
qualification of a canonical source does not qualify historical guide variants.

Run from Gamma:

```sh
python3 projects/algorithm_solver/literals/fragment-spelling-v1/test_codec.py
```
