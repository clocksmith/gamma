"""2030. Smallest K-Length Subsequence With Occurrences of a Letter."""


def solve(s: str, k: int, letter: str, repetition: int) -> str:
    """Quota-aware monotonic stack; O(n) time and O(k) space. Inputs are preserved."""
    remaining = s.count(letter)
    needed = repetition
    stack = []
    for index, character in enumerate(s):
        while (stack and stack[-1] > character
               and len(stack) - 1 + len(s) - index >= k
               and (stack[-1] != letter or remaining > needed)):
            if stack.pop() == letter:
                needed += 1
        if len(stack) < k:
            if character == letter:
                stack.append(character)
                needed -= 1
            elif k - len(stack) > needed:
                stack.append(character)
        if character == letter:
            remaining -= 1
    return ''.join(stack)


class Solution:
    def smallestSubsequence(self, s: str, k: int, letter: str, repetition: int) -> str:
        return solve(s, k, letter, repetition)
