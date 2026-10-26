"""1807. Evaluate the Bracket Pairs of a String: substitute bracketed keys while leaving ordinary text untouched."""


def solve(s: str, knowledge: list[list[str]]) -> str:
    """O(n + K + R) expected time and space, with K knowledge size and R output length; inputs are read-only."""
    values = dict(knowledge)
    result = []
    index = 0
    while index < len(s):
        if s[index] != '(':
            result.append(s[index])
            index += 1
            continue
        end = s.index(')', index + 1)
        result.append(values.get(s[index + 1:end], '?'))
        index = end + 1
    return ''.join(result)


class Solution:
    def evaluate(self, s: str, knowledge: list[list[str]]) -> str:
        return solve(s, knowledge)
