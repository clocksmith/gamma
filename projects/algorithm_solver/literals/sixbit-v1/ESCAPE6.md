# Codec literal-escape6-v1

A separately specified six-bit codec for experiment C. It does not change the
canonical LTD1/LTV1 codec ([bitpack.py](../pass2/working/bitpack.py),
[literal_codec.py](../readable-v1/literal_codec.py)) or anything in BITS.

## Codes

- Payload width 6 bits. Codes 0..62 select dictionary entries 0..62 (at most 63
  entries). Code 63 is `ESC`.
- After `ESC`, exactly 7 raw bits follow: an ASCII code point. Only 10 (newline) and
  32..126 are valid; a decoder rejects every other value.

## Input presses (BITS framing)

BITS sends one frame bit before every payload so control frames stay separate.

| Token | Frames | Presses |
| --- | --- | ---: |
| dictionary selection | frame bit + 6-bit code | 7 |
| escaped character | `ESC` frame (7) + frame bit + 7-bit ASCII code (8) | 15 |

Every escape is charged both frames. Control frames (undo, reset, finish) are outside
this measurement, as for every other profile compared here.

## Stored bytes

- Dictionary: canonical LTD1 bytes, unchanged.
- Packet: `LTE6` (4 bytes), SHA-256 of the LTD1 dictionary (32), token count as a
  big-endian 32-bit integer (4), then the payload bits (6 per selection, 6 + 7 per
  escape) packed most significant bit first, zero-padded to a byte.
- Decoder: the reference decoder [escape6_decoder.py](escape6_decoder.py) is new code
  that a client would need, so its file bytes are charged once in the package:
  package bytes = decoder bytes + dictionary bytes + all packet bytes. The package is
  also reported without the decoder, matching how live profiles report package bytes
  (their canonical decoder is shared and constant).

## Encoder

[escape6.py](escape6.py) writes packets; the experiment's exact dynamic program picks
tokens that minimize presses for a fixed dictionary (ties: fewer escapes, then the
shorter first piece).
