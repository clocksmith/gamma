"""293. Flip Game (Easy).

Specification: https://leetcode.com/problems/flip-game/description/
"""


def solve(currentState: str) -> list[str]:
    """O(n^2) worst-case time and result space; emit moves in increasing flipped-index order."""
    result = []
    for index in range(len(currentState) - 1):
        if currentState[index:index + 2] == '++':
            result.append(currentState[:index] + '--' + currentState[index + 2:])
    return result


class Solution:
    def generatePossibleNextMoves(self, currentState: str) -> list[str]:
        return solve(currentState)
