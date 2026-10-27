"""Exact UTF-8 fragments with a fully charged binary spelling mode.

ID 0 opens spelling (width bits). In spelling, 1 + eight bits appends a byte;
0 closes spelling (one bit). Other IDs append exact dictionary fragments.
This is a hybrid representation, not a pure width-bit literal dictionary.
"""
from dataclasses import dataclass
from hashlib import sha256

MAX_FRAGMENT_BYTES = 512
MAX_SOURCE_BYTES = 65536
MAX_BITS = MAX_SOURCE_BYTES * 10 + 32


def validate_dictionary(fragments, width):
    if width not in (6, 7, 8):
        raise ValueError('Fragment width must be 6, 7 or 8')
    if not isinstance(fragments, (list, tuple)) or len(fragments) != (1 << width) - 1:
        raise ValueError('One code is reserved for spelling; exact fragment slot count required')
    if any(not isinstance(text, str) or len(text) < 2 for text in fragments):
        raise ValueError('Fragments must contain at least two Unicode characters')
    if len(set(fragments)) != len(fragments):
        raise ValueError('Dictionary fragments must be unique')
    for text in fragments:
        if len(text.encode('utf-8', errors='strict')) > MAX_FRAGMENT_BYTES:
            raise ValueError('Fragment exceeds 512 UTF-8 bytes')
    return tuple(text.encode('utf-8') for text in fragments)


@dataclass(frozen=True)
class Packet:
    width: int
    bits: str
    source_sha256: str
    source_bytes: int
    fragment_selections: int
    fragment_bits: int
    spelling_bytes: int
    spelling_bits: int
    mode_switch_bits: int

    @property
    def input_presses(self):
        return len(self.bits)


def encode(source, fragments, width):
    """Minimum binary press parse; fitting/qualification are outside this codec.

    Two states at each UTF-8 byte boundary, at most 64KiB. Ties keep the first
    action: lower fragment ID before spelling; no uncharged names or operands.
    O(source bytes * dictionary size + matching bytes), O(source bytes) state.
    """
    dictionary = validate_dictionary(fragments, width)
    raw = source.encode('utf-8', errors='strict')
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError('Source exceeds 64KiB')
    n = len(raw)
    normal, spelling = [0] * (n + 1), [0] * (n + 1)
    selected, keep_spelling = [0] * n, [False] * n
    spelling[n] = 1  # Closing spelling is mandatory, including at EOF.
    for offset in range(n - 1, -1, -1):
        best, choice = width + 9 + spelling[offset + 1], 0
        for index, fragment in enumerate(dictionary, 1):
            if raw.startswith(fragment, offset):
                cost = width + normal[offset + len(fragment)]
                if cost < best or (cost == best and (choice == 0 or index < choice)):
                    best, choice = cost, index
        normal[offset], selected[offset] = best, choice
        # Exit may immediately select a fragment or open a new spelling run.
        # Reopening is costlier than staying, so no zero-length cycle exists.
        stay, leave = 9 + spelling[offset + 1], 1 + normal[offset]
        spelling[offset], keep_spelling[offset] = (stay, True) if stay < leave else (leave, False)
    bits, offset, in_spelling = [], 0, False
    fragments_used = bytes_spelled = switches = 0
    while offset < n:
        if in_spelling:
            if keep_spelling[offset]:
                bits.append('1' + format(raw[offset], '08b'))
                bytes_spelled += 1
                offset += 1
            else:
                bits.append('0'); switches += 1; in_spelling = False
        else:
            entry = selected[offset]
            bits.append(format(entry, f'0{width}b'))
            if entry:
                offset += len(dictionary[entry - 1]); fragments_used += 1
            else:
                switches += width; in_spelling = True
                bits.append('1' + format(raw[offset], '08b'))
                bytes_spelled += 1; offset += 1
    if in_spelling:
        bits.append('0'); switches += 1
    encoded = ''.join(bits)
    assert len(encoded) == normal[0]
    assert decode(encoded, fragments, width) == source
    return Packet(width, encoded, sha256(raw).hexdigest(), n, fragments_used,
                  fragments_used * width, bytes_spelled, bytes_spelled * 9, switches)


def decode(bits, fragments, width):
    dictionary = validate_dictionary(fragments, width)
    if not isinstance(bits, str) or len(bits) > MAX_BITS or any(bit not in '01' for bit in bits):
        raise ValueError('Invalid or oversized binary input')
    output, offset, in_spelling = bytearray(), 0, False
    while offset < len(bits):
        if in_spelling:
            flag = bits[offset]; offset += 1
            if flag == '0':
                in_spelling = False
            else:
                if offset + 8 > len(bits):
                    raise ValueError('Incomplete spelling byte')
                output.append(int(bits[offset:offset + 8], 2)); offset += 8
        else:
            if offset + width > len(bits):
                raise ValueError('Incomplete fragment ID')
            entry = int(bits[offset:offset + width], 2); offset += width
            if entry == 0:
                in_spelling = True
            else:
                output.extend(dictionary[entry - 1])
        if len(output) > MAX_SOURCE_BYTES:
            raise ValueError('Decoded source exceeds 64KiB')
    if in_spelling:
        raise ValueError('Spelling mode must close before Finish')
    return output.decode('utf-8', errors='strict')


def dictionary_bytes(fragments, width):
    values = validate_dictionary(fragments, width)
    return b'FSD1' + bytes([width]) + len(values).to_bytes(2, 'big') + b''.join(
        len(value).to_bytes(4, 'big') + value for value in values)


def packet_bytes(packet):
    padding = (-len(packet.bits)) % 8
    payload = int(packet.bits + '0' * padding, 2).to_bytes((len(packet.bits) + 7) // 8, 'big') if packet.bits else b''
    return b'FSP1' + bytes([packet.width]) + len(packet.bits).to_bytes(4, 'big') + payload


def decode_packet(data, fragments, width):
    if not isinstance(data, bytes) or len(data) < 9 or data[:5] != b'FSP1' + bytes([width]):
        raise ValueError('Packet protocol/width mismatch')
    length = int.from_bytes(data[5:9], 'big')
    if length > MAX_BITS or len(data) != 9 + (length + 7) // 8:
        raise ValueError('Packet length mismatch')
    bits = ''.join(format(byte, '08b') for byte in data[9:])
    if '1' in bits[length:]:
        raise ValueError('Nonzero packet padding')
    return decode(bits[:length], fragments, width)
