"""798. Smallest Rotation with Highest Score."""

def solve(nums: list[int]) -> int:
    """O(n) time and space; count each element's circular interval of bad rotations."""
    size = len(nums)
    changes = [0] * (size + 1)
    for index, value in enumerate(nums):
        if value == 0:
            continue
        left = (index - value + 1) % size
        right = (index + 1) % size
        if left < right:
            changes[left] += 1
            changes[right] -= 1
        else:
            changes[0] += 1
            changes[right] -= 1
            changes[left] += 1
            changes[size] -= 1
    bad = 0
    best_bad = size + 1
    answer = 0
    for rotation in range(size):
        bad += changes[rotation]
        if bad < best_bad:
            best_bad = bad
            answer = rotation
    return answer


class Solution:
    def bestRotation(self, nums: list[int]) -> int:
        return solve(nums)
