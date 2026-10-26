"""2106. Maximum Fruits Harvested After at Most K Steps."""


def solve(fruits: list[list[int]], startPos: int, k: int) -> int:
    """Sliding window with the cheaper of the two one-turn routes; O(n) time and O(1) auxiliary space. Inputs are preserved."""
    left = 0
    total = 0
    answer = 0
    for right, (position, amount) in enumerate(fruits):
        total += amount
        while left <= right:
            west = max(0, startPos - fruits[left][0])
            east = max(0, position - startPos)
            if west + east + min(west, east) <= k:
                break
            total -= fruits[left][1]
            left += 1
        answer = max(answer, total)
    return answer


class Solution:
    def maxTotalFruits(self, fruits: list[list[int]], startPos: int, k: int) -> int:
        return solve(fruits, startPos, k)
