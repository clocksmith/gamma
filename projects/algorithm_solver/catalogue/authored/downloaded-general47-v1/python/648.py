"""648. Replace Words (Medium).

Specification: https://leetcode.com/problems/replace-words/description/
"""


def solve(dictionary: list[str], sentence: str) -> str:
    roots = set(dictionary)
    result = []
    for word in sentence.split(' '):
        replacement = word
        for length in range(1, len(word) + 1):
            prefix = word[:length]
            if prefix in roots:
                replacement = prefix
                break
        result.append(replacement)
    return " ".join(result)


class Solution:
    def replaceWords(self, dictionary: list[str], sentence: str) -> str:
        return solve(dictionary, sentence)
