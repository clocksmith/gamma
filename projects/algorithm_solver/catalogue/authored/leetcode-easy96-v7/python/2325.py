"""2325. Decode the Message (Easy).

Specification: https://leetcode.com/problems/decode-the-message/description/
"""


def solve(key: str, message: str) -> str:
    """O(k + m) time, O(m) result space; map first occurrences of lowercase key letters; keep spaces."""
    mapping = {}
    next_letter = 0
    for character in key:
        if character != ' ' and character not in mapping:
            mapping[character] = chr(97 + next_letter)
            next_letter += 1
    return ''.join(' ' if character == ' ' else mapping[character] for character in message)


class Solution:
    def decodeMessage(self, key: str, message: str) -> str:
        return solve(key, message)
