"""2287. Rearrange Characters to Make Target String (Easy).

Specification: https://leetcode.com/problems/rearrange-characters-to-make-target-string/description/
"""


def solve(s: str, target: str) -> int:
    """O(n + m) time, O(1) alphabet space; the scarcest required letter limits complete copies."""
    available = [0] * 26
    required = [0] * 26
    for character in s:
        available[ord(character) - 97] += 1
    for character in target:
        required[ord(character) - 97] += 1
    copies = len(s)
    for letter in range(26):
        if required[letter] > 0:
            copies = min(copies, available[letter] // required[letter])
    return copies


class Solution:
    def rearrangeCharacters(self, s: str, target: str) -> int:
        return solve(s, target)
