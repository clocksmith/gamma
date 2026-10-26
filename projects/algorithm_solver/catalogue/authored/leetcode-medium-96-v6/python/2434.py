"""2434. Using a Robot to Print the Lexicographically Smallest String: release stack letters whenever they do not exceed the smallest remaining input letter."""


def solve(s: str) -> str:
    """O(n + 26) time and O(n + 26) auxiliary and result space; inputs are read-only."""
    remaining = [0] * 26
    for character in s:
        remaining[ord(character) - ord('a')] += 1
    smallest = 0
    stack = []
    result = []
    for character in s:
        letter = ord(character) - ord('a')
        stack.append(letter)
        remaining[letter] -= 1
        while smallest < 26 and remaining[smallest] == 0:
            smallest += 1
        while stack and stack[-1] <= smallest:
            result.append(chr(ord('a') + stack.pop()))
    return ''.join(result)


class Solution:
    def robotWithString(self, s: str) -> str:
        return solve(s)
