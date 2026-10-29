"""Hack2Hire 69ff8062574d87bc49006e92 (Restore String with Target Digit Sum) over an INFERRED spec; qualification unknown."""


def solve(pattern, targetSum, maxVal):
    slots = pattern.count('?')
    rest = targetSum - sum(int(ch) for ch in pattern if ch != '?')
    if rest < 0 or rest > slots * maxVal:
        return ''
    out = []
    for ch in pattern:
        if ch != '?':
            out.append(ch)
            continue
        slots -= 1
        digit = max(0, rest - slots * maxVal)
        out.append(str(digit))
        rest -= digit
    return ''.join(out)


class Solution:
    def restoreString(self, pattern, targetSum, maxVal):
        return solve(pattern, targetSum, maxVal)
