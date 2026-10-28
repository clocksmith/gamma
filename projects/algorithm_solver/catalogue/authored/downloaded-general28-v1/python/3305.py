"""3305. Count of Substrings Containing Every Vowel and K Consonants I (Medium).

Specification: https://leetcode.com/problems/count-of-substrings-containing-every-vowel-and-k-consonants-i/description/
"""


def solve(word: str, k: int) -> int:
    vowels = set('aeiou')
    ans = 0
    for i in range(len(word)):
        seen = set()
        cons = 0
        for j in range(i, len(word)):
            if word[j] in vowels:
                seen.add(word[j])
            else:
                cons += 1
            if len(seen) == 5 and cons == k:
                ans += 1
            if cons > k:
                break
    return ans


class Solution:
    def countOfSubstrings(self, word: str, k: int) -> int:
        return solve(word, k)
