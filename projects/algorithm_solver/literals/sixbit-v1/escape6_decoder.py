"""Reference decoder for literal-escape6-v1 (ESCAPE6.md). Its file bytes are charged."""
import hashlib
import struct


def decode(dictionary, packet):
    if dictionary[:4] != b'LTD1' or packet[:4] != b'LTE6' or len(packet) < 40:
        raise ValueError('header')
    if packet[4:36] != hashlib.sha256(dictionary).digest():
        raise ValueError('dictionary hash')
    count, at, entries = struct.unpack_from('>I', dictionary, 4)[0], 8, []
    if count > 63:
        raise ValueError('more than 63 entries')
    for _ in range(count):
        size = struct.unpack_from('>I', dictionary, at)[0]
        entries.append(dictionary[at + 4:at + 4 + size].decode('utf-8'))
        at += 4 + size
    if at != len(dictionary):
        raise ValueError('dictionary length')
    bits, pos, out = ''.join(format(b, '08b') for b in packet[40:]), 0, []

    def take(width):
        nonlocal pos
        if pos + width > len(bits):
            raise ValueError('truncated')
        pos += width
        return int(bits[pos - width:pos], 2)

    for _ in range(struct.unpack_from('>I', packet, 36)[0]):
        code = take(6)
        if code == 63:
            raw = take(7)
            if raw != 10 and not 32 <= raw <= 126:
                raise ValueError('escape code')
            out.append(chr(raw))
        elif code < count:
            out.append(entries[code])
        else:
            raise ValueError('unassigned code')
    if len(bits) - pos >= 8 or '1' in bits[pos:]:
        raise ValueError('padding')
    return ''.join(out)
