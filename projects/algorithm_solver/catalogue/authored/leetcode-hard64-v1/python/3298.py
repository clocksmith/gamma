"""3298. Count Substrings That Can Be Rearranged to Contain a String II: multiplicity-aware sliding window."""


def solve(word1: str, word2: str) -> int:
    """O(n + m) time and O(26) auxiliary space. Inputs are preserved."""
    needed = [0] * 26
    for character in word2:
        needed[ord(character) - ord('a')] += 1
    missing = len(word2)
    left = 0
    answer = 0
    for character in word1:
        letter = ord(character) - ord('a')
        if needed[letter] > 0:
            missing -= 1
        needed[letter] -= 1
        while missing == 0:
            letter = ord(word1[left]) - ord('a')
            needed[letter] += 1
            if needed[letter] > 0:
                missing += 1
            left += 1
        answer += left
    return answer


class Solution:
    def validSubstringCount(self, word1: str, word2: str) -> int:
        return solve(word1, word2)
