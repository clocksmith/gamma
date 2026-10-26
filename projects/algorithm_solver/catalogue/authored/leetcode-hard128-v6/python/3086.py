"""3086. Minimum Moves to Pick K Ones.

Use up to three adjacent ones cheaply, otherwise gather a median window and create the remainder; O(n) time and space. Inputs are preserved.
"""

def solve(nums: list[int], k: int, maxChanges: int) -> int:
    positions = []
    run = longest = 0
    for index, value in enumerate(nums):
        if value:
            positions.append(index)
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    nearby = min(k, 3, longest)
    if maxChanges >= k - nearby:
        return max(0, nearby - 1) + 2 * (k - nearby)
    required = k - maxChanges
    prefix = [0]
    for position in positions:
        prefix.append(prefix[-1] + position)
    answer = float('inf')
    for left in range(len(positions) - required + 1):
        right = left + required
        middle = (left + right - 1) // 2
        distance = (positions[middle] * (middle - left) - prefix[middle] + prefix[left]
                    + prefix[right] - prefix[middle + 1] - positions[middle] * (right - middle - 1))
        answer = min(answer, distance + 2 * maxChanges)
    return answer


class Solution:
    def minimumMoves(self, nums: list[int], k: int, maxChanges: int) -> int:
        return solve(nums, k, maxChanges)
