"""1441. Build an Array With Stack Operations: emit pushes for the stream and pops for values absent from the target."""


def solve(target: list[int], n: int) -> list[str]:
    """O(target[-1]) time and O(target[-1]) space including the result; inputs are read-only."""
    result = []
    value = 1
    for wanted in target:
        while value < wanted:
            result.extend(('Push', 'Pop'))
            value += 1
        result.append('Push')
        value += 1
    return result


class Solution:
    def buildArray(self, target: list[int], n: int) -> list[str]:
        return solve(target, n)
