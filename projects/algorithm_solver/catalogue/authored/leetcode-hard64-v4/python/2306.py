"""2306. Naming a Company."""


def solve(ideas: list[str]) -> int:
    """Count nonshared suffixes between initial-letter groups; O(L+26*n) time and O(L+n) space. Inputs are preserved."""
    groups = [set() for _ in range(26)]
    for word in ideas:
        groups[ord(word[0]) - ord('a')].add(word[1:])
    answer = 0
    for first in range(26):
        for second in range(first + 1, 26):
            common = len(groups[first] & groups[second])
            answer += 2 * (len(groups[first]) - common) * (len(groups[second]) - common)
    return answer


class Solution:
    def distinctNames(self, ideas: list[str]) -> int:
        return solve(ideas)
