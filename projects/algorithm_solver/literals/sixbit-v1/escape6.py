"""Encoder and press accounting for literal-escape6-v1 (ESCAPE6.md).

Separate from the canonical LTV1 codec, which is unchanged."""
import hashlib
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CODEC = 'literal-escape6-v1'
ESC = 63
SELECTION_PRESSES = 7      # frame bit + 6-bit code
ESCAPE_PRESSES = 7 + 8     # ESC frame, then frame bit + 7-bit ASCII code
DECODER = ROOT / 'escape6_decoder.py'


def encode(dictionary, entries, tokens):
    """tokens: ('d', entry index) or ('e', character)."""
    if len(entries) > 63:
        raise ValueError('more than 63 entries')
    bits = []
    for kind, value in tokens:
        if kind == 'd':
            if not 0 <= value < len(entries):
                raise ValueError('entry index')
            bits.append(format(value, '06b'))
        else:
            code = ord(value)
            if code != 10 and not 32 <= code <= 126:
                raise ValueError('escape code')
            bits.append(format(ESC, '06b') + format(code, '07b'))
    stream = ''.join(bits)
    stream += '0' * (-len(stream) % 8)
    payload = bytes(int(stream[i:i + 8], 2) for i in range(0, len(stream), 8))
    return b'LTE6' + hashlib.sha256(dictionary).digest() + struct.pack('>I', len(tokens)) + payload


def presses(tokens):
    escapes = sum(kind == 'e' for kind, _ in tokens)
    return SELECTION_PRESSES * (len(tokens) - escapes) + ESCAPE_PRESSES * escapes


def decoder_bytes():
    return DECODER.stat().st_size
