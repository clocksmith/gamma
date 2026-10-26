"""1160. Find Words That Can Be Formed by Characters (Easy).

Specification: https://leetcode.com/problems/find-words-that-can-be-formed-by-characters/description/
"""


def solve(words: list[str], chars: str) -> int:
    """O(total characters) time, O(1) alphabet space; reset letter usage for each word."""
    available = [0] * 26
    for character in chars:
        available[ord(character) - 97] += 1
    total = 0
    for word in words:
        used = [0] * 26
        valid = True
        for character in word:
            letter = ord(character) - 97
            used[letter] += 1
            if used[letter] > available[letter]:
                valid = False
                break
        if valid:
            total += len(word)
    return total


class Solution:
    def countCharacters(self, words: list[str], chars: str) -> int:
        return solve(words, chars)
