"""804. Unique Morse Code Words (Easy).

Specification: https://leetcode.com/problems/unique-morse-code-words/description/
"""


def solve(words: list[str]) -> int:
    """O(s) expected time and O(s) space, where s is total input length; preserve the word list."""
    codes = (
        '.-', '-...', '-.-.', '-..', '.', '..-.', '--.', '....', '..', '.---',
        '-.-', '.-..', '--', '-.', '---', '.--.', '--.-', '.-.', '...', '-',
        '..-', '...-', '.--', '-..-', '-.--', '--..'
    )
    representations = set()
    for word in words:
        representation = ''.join(codes[ord(letter) - 97] for letter in word)
        representations.add(representation)
    return len(representations)


class Solution:
    def uniqueMorseRepresentations(self, words: list[str]) -> int:
        return solve(words)
