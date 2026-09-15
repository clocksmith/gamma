"""Exact expert validity-likelihood correction; no trained or adaptive state."""
import struct

Q = 65536
SCALE = 1 << 43
MINIMUM = 8796093  # exact binary32 1e-6f expressed in units of 2**-43


def half_mass(h):
    if h == 0x8000: h = 0
    if not 0 <= h <= 0x3c00:
        raise ValueError('expert entry outside finite [0,1]')
    e, m = h >> 10, h & 1023
    value = (m << 19) if e == 0 else ((1024+m) << (e+18))
    return max(MINIMUM, value)


def row_masses(row, vocabulary, rotate=False):
    if len(row) != len(vocabulary)*2 or sorted(set(vocabulary)) != list(vocabulary):
        raise ValueError('expert row or vocabulary differs')
    weights = [half_mass(h) for (h,) in struct.iter_unpack('<H', row)]
    if not SCALE//2 <= sum(weights) <= 2*SCALE:
        raise ValueError('expert row outside declared normalization envelope')
    if rotate: weights = weights[1:]+weights[:1]
    masses = [0]*256
    for c, w in zip(vocabulary, weights): masses[c] = w
    return masses


def prefixes(masses, allowed):
    if len(masses) != 256 or not 0 < allowed < 1 << 256:
        raise ValueError('invalid mass or support population')
    original, legal = [0], [0]
    for c, w in enumerate(masses):
        original.append(original[-1]+w)
        legal.append(legal[-1]+(w if (allowed >> c) & 1 else 0))
    if not 0 < legal[-1] <= original[-1] <= 2*SCALE:
        raise ValueError('empty or excessive legal mass')
    return original, legal


def branch_masses(prefix, cdf):
    if not 1 <= prefix < 256 or len(cdf) != 257:
        raise ValueError('invalid binary prefix')
    depth = prefix.bit_length()-1
    width = 1 << (8-depth)
    start = (prefix-(1 << depth))*width
    mid, end = start+width//2, start+width
    return cdf[mid]-cdf[start], cdf[end]-cdf[mid]


def corrected_count(parent, c0, c1, a0, a1):
    if not 1 <= parent < Q or not 0 < c0 <= 2*SCALE or not 0 < c1 <= 2*SCALE:
        raise ValueError('invalid parent count or branch mass')
    if not 0 < a0 <= c0 or not 0 < a1 <= c1 or c0+c1 > 2*SCALE:
        raise ValueError('ambiguous legal branches required')
    a = parent*a1*c0
    b = (Q-parent)*a0*c1
    return min(Q-1, max(1, (Q*a+(a+b)//2)//(a+b)))


def correct(parent, prefix, original, legal):
    c0, c1 = branch_masses(prefix, original)
    a0, a1 = branch_masses(prefix, legal)
    return corrected_count(parent, c0, c1, a0, a1)
