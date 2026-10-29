"""Hack2Hire 6887e0fc6509c24ee64e4b21 (String Reorganization) over an INFERRED spec; qualification unknown."""


def solve(s):
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - 97] += 1
    n = len(s)
    if max(counts) > (n + 1) // 2:
        return ''
    out = []
    previous = -1
    lowest = 0
    remaining = n
    for _ in range(n):
        while counts[lowest] == 0:
            lowest += 1
        top = max(counts)
        holders = counts.count(top)
        after = remaining - 1
        half = (after + 1) // 2
        for c in range(lowest, 26):
            if c == previous or counts[c] == 0:
                continue
            new_top = top - 1 if counts[c] == top and holders == 1 else top
            left_c = counts[c] - 1
            if new_top <= half and not (after % 2 == 1 and left_c == half):
                counts[c] = left_c
                out.append(chr(97 + c))
                previous = c
                remaining = after
                break
    return ''.join(out)


class Solution:
    def reorganize(self, s):
        return solve(s)
