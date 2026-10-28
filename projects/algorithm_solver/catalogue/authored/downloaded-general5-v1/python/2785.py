"""2785. Sort Vowels in a String (Medium).

Specification: https://leetcode.com/problems/sort-vowels-in-a-string/description/
"""


def solve(s: str) -> str:
    vowels = set('aeiouAEIOU')
    found = sorted(ch for ch in s if ch in vowels)
    k = 0
    out = []
    for ch in s:
        if ch in vowels:
            out.append(found[k])
            k += 1
        else:
            out.append(ch)
    return ''.join(out)


class Solution:
    def sortVowels(self, s: str) -> str:
        return solve(s)
