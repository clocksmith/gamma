"""3219. Minimum Cost for Cutting Cake II.

Take the most expensive remaining cut before multiplying perpendicular pieces; O(m log m+n log n) time and O(m+n) space. Inputs are preserved.
"""

def solve(m: int, n: int, horizontalCut: list[int], verticalCut: list[int]) -> int:
    horizontal = sorted(horizontalCut, reverse=True)
    vertical = sorted(verticalCut, reverse=True)
    first = second = 0
    answer = 0
    while first < len(horizontal) or second < len(vertical):
        if second == len(vertical) or (first < len(horizontal) and horizontal[first] >= vertical[second]):
            answer += horizontal[first] * (second + 1)
            first += 1
        else:
            answer += vertical[second] * (first + 1)
            second += 1
    return answer


class Solution:
    def minimumCost(self, m: int, n: int, horizontalCut: list[int], verticalCut: list[int]) -> int:
        return solve(m, n, horizontalCut, verticalCut)
