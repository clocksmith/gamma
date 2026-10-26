"""1371. Find the Longest Substring Containing Vowels in Even Counts: match the earliest occurrence of each vowel-parity mask."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space for 32 masks; inputs are read-only."""
    bits = {'a': 1, 'e': 2, 'i': 4, 'o': 8, 'u': 16}
    first = [-2] * 32
    first[0] = -1
    mask = answer = 0
    for index, character in enumerate(s):
        mask ^= bits.get(character, 0)
        if first[mask] == -2:
            first[mask] = index
        else:
            answer = max(answer, index - first[mask])
    return answer


class Solution:
    def findTheLongestSubstring(self, s: str) -> int:
        return solve(s)
