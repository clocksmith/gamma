def solve(nums: list[int]) -> list[int]:
    """Count opposite-parity values in each suffix. O(n) time, O(n) output."""
    counts = [0, 0]
    answer = [0] * len(nums)
    for index in range(len(nums) - 1, -1, -1):
        parity = nums[index] % 2
        answer[index] = counts[1 - parity]
        counts[parity] += 1
    return answer
