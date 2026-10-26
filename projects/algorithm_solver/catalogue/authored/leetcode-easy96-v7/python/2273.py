"""2273. Find Resultant Array After Removing Anagrams (Easy).

Specification: https://leetcode.com/problems/find-resultant-array-after-removing-anagrams/description/
"""


def solve(words: list[str]) -> list[str]:
    """O(total characters + 26n) time, O(n) result references; compare adjacent retained signatures; preserve words."""
    result = []
    previous = None
    for word in words:
        counts = [0] * 26
        for character in word:
            counts[ord(character) - 97] += 1
        signature = tuple(counts)
        if signature != previous:
            result.append(word)
            previous = signature
    return result


class Solution:
    def removeAnagrams(self, words: list[str]) -> list[str]:
        return solve(words)
