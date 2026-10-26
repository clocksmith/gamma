"""2047. Number of Valid Words in a Sentence (Easy).

Specification: https://leetcode.com/problems/number-of-valid-words-in-a-sentence/description/
"""


def solve(sentence: str) -> int:
    """O(n) time and O(n) token storage; apply the lowercase ASCII token rules."""
    result = 0
    for token in sentence.split():
        valid = True
        hyphens = 0
        for index, character in enumerate(token):
            if '0' <= character <= '9':
                valid = False
                break
            if character == '-':
                hyphens += 1
                if (hyphens > 1 or index == 0 or index + 1 == len(token)
                        or not 'a' <= token[index - 1] <= 'z'
                        or not 'a' <= token[index + 1] <= 'z'):
                    valid = False
                    break
            elif character in '!.,':
                if index + 1 != len(token):
                    valid = False
                    break
        if valid:
            result += 1
    return result


class Solution:
    def countValidWords(self, sentence: str) -> int:
        return solve(sentence)
