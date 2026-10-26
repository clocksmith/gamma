"""2193. Minimum Number of Moves to Make Palindrome."""


def solve(s: str) -> int:
    """Greedy matching from both ends using adjacent swaps; O(n^2) time and O(n) space. Inputs are preserved."""
    characters = list(s)
    left, right = 0, len(characters) - 1
    moves = 0
    while left < right:
        match = right
        while characters[match] != characters[left]:
            match -= 1
        if match == left:
            characters[left], characters[left + 1] = characters[left + 1], characters[left]
            moves += 1
            continue
        for index in range(match, right):
            characters[index], characters[index + 1] = characters[index + 1], characters[index]
        moves += right - match
        left += 1
        right -= 1
    return moves


class Solution:
    def minMovesToMakePalindrome(self, s: str) -> int:
        return solve(s)
