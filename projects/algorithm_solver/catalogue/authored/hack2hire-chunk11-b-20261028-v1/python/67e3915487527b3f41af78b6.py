"""Hack2Hire 67e3915487527b3f41af78b6 (Keypad Letter Combination) over an INFERRED spec; qualification unknown."""


_KEYPAD = {'1': 'ABC', '2': 'DEF', '3': 'GHI', '4': 'JKL', '5': 'MNO', '6': 'PQR', '7': 'ST', '8': 'UVW', '9': 'XY', '0': 'Z'}


def solve(digits):
    n = len(digits)
    if n == 0:
        return []
    out = []
    letters = []

    def extend(i):
        # smaller groups give smaller letters, so results come out in lexicographic order
        if i == n:
            out.append(''.join(letters))
            return
        keys = _KEYPAD[digits[i]]
        g = 1
        while g <= len(keys) and i + g <= n and digits[i + g - 1] == digits[i]:
            letters.append(keys[g - 1])
            extend(i + g)
            letters.pop()
            g += 1
    extend(0)
    return out


class Solution:
    def letterCombinations(self, digits):
        return solve(digits)
