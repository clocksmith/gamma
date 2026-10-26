"""2059. Minimum Operations to Convert Number: breadth-first search bounded intermediate states while allowing an out-of-range final result."""


def solve(nums: list[int], start: int, goal: int) -> int:
    """O(B * n) time and O(B) auxiliary space for B = 1001 permitted intermediate values; inputs are read-only."""
    if start == goal:
        return 0
    seen = bytearray(1001)
    seen[start] = 1
    queue = [start]
    head = steps = 0
    while head < len(queue):
        layer_end = len(queue)
        steps += 1
        while head < layer_end:
            current = queue[head]
            head += 1
            for value in nums:
                for candidate in (current + value, current - value, current ^ value):
                    if candidate == goal:
                        return steps
                    if 0 <= candidate <= 1000 and not seen[candidate]:
                        seen[candidate] = 1
                        queue.append(candidate)
    return -1


class Solution:
    def minimumOperations(self, nums: list[int], start: int, goal: int) -> int:
        return solve(nums, start, goal)
