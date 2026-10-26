"""2398. Maximum Number of Robots Within Budget. Sliding window with a monotonic maximum queue."""

from collections import deque


def solve(chargeTimes: list[int], runningCosts: list[int], budget: int) -> int:
    """O(n) time and O(n) space. Inputs are preserved."""
    maximums = deque()
    left = 0
    running = 0
    answer = 0
    for right, charge in enumerate(chargeTimes):
        while maximums and chargeTimes[maximums[-1]] <= charge:
            maximums.pop()
        maximums.append(right)
        running += runningCosts[right]
        while left <= right and chargeTimes[maximums[0]] + (right - left + 1) * running > budget:
            if maximums[0] == left:
                maximums.popleft()
            running -= runningCosts[left]
            left += 1
        answer = max(answer, right - left + 1)
    return answer


class Solution:
    def maximumRobots(self, chargeTimes: list[int], runningCosts: list[int], budget: int) -> int:
        return solve(chargeTimes, runningCosts, budget)
