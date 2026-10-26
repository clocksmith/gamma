"""1910. Remove All Occurrences of a Substring: retain prefix-match states beside the output stack for linear-time removal."""


def solve(s: str, part: str) -> str:
    """O(len(s) + len(part)) time and auxiliary space; inputs are read-only."""
    failure = [0] * len(part)
    matched = 0
    for index in range(1, len(part)):
        while matched and part[index] != part[matched]:
            matched = failure[matched - 1]
        if part[index] == part[matched]:
            matched += 1
        failure[index] = matched
    output = []
    states = []
    matched = 0
    for letter in s:
        while matched and letter != part[matched]:
            matched = failure[matched - 1]
        if letter == part[matched]:
            matched += 1
        output.append(letter)
        states.append(matched)
        if matched == len(part):
            del output[-len(part):]
            del states[-len(part):]
            matched = states[-1] if states else 0
    return ''.join(output)


class Solution:
    def removeOccurrences(self, s: str, part: str) -> str:
        return solve(s, part)
