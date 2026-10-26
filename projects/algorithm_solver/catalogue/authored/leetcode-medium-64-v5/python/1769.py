"""1769. Minimum Number of Operations to Move All Balls to Each Box: accumulate movement costs in one sweep from each side."""


def solve(boxes: str) -> list[int]:
    """O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only."""
    result = [0] * len(boxes)
    balls = cost = 0
    for index, value in enumerate(boxes):
        result[index] += cost
        balls += value == '1'
        cost += balls
    balls = cost = 0
    for index in range(len(boxes) - 1, -1, -1):
        result[index] += cost
        balls += boxes[index] == '1'
        cost += balls
    return result


class Solution:
    def minOperations(self, boxes: str) -> list[int]:
        return solve(boxes)
