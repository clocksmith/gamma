"""3734. Lexicographically Smallest Palindromic Permutation Greater Than Target
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/lexicographically-smallest-palindromic-permutation-greater-than-target/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3734.Lexicographically%20Smallest%20Palindromic%20Permutation%20Greater%20Than%20Target/README_EN.md
Complexity: O(26n) time; O(n) space.
Equal-length lowercase strings; strict comparison; returns empty string when impossible.
"""

from __future__ import annotations

def solve(s, target):
    counts = [0] * 26
    for character in s:
        counts[ord(character) - 97] += 1
    odd = [index for index, count in enumerate(counts) if count % 2]
    if len(odd) > 1:
        return ''
    center = chr(97 + odd[0]) if odd else ''
    remaining = [count // 2 for count in counts]
    half_length = len(s) // 2
    prefix = []
    while len(prefix) < half_length:
        index = ord(target[len(prefix)]) - 97
        if remaining[index] == 0:
            break
        remaining[index] -= 1
        prefix.append(target[len(prefix)])
    if len(prefix) == half_length:
        left = ''.join(prefix)
        candidate = left + center + left[::-1]
        if candidate > target:
            return candidate
    position = len(prefix)
    while position >= 0:
        if position < half_length:
            for index in range(ord(target[position]) - 96, 26):
                if remaining[index]:
                    remaining[index] -= 1
                    left = ''.join(prefix) + chr(97 + index)
                    left += ''.join(chr(97 + letter) * count for letter, count in enumerate(remaining))
                    return left + center + left[::-1]
        if not prefix:
            break
        removed = prefix.pop()
        remaining[ord(removed) - 97] += 1
        position -= 1
    return ''


class Solution:
    def lexPalindromicPermutation(self, s, target):
        return solve(s, target)
