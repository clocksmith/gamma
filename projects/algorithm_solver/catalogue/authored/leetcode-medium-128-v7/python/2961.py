"""2961. Double Modular Exponentiation: evaluate the two modular exponentiations without constructing the full powers."""


def solve(variables: list[list[int]], target: int) -> list[int]:
    """O(n * (log B + log C)) time and O(n) auxiliary space including the result; inputs are read-only."""
    result = []
    for index, (a, b, c, m) in enumerate(variables):
        if pow(pow(a, b, 10), c, m) == target:
            result.append(index)
    return result


class Solution:
    def getGoodIndices(self, variables: list[list[int]], target: int) -> list[int]:
        return solve(variables, target)
