def solve(nums: list[int]) -> int:
    """Each zero in the nonzero prefix requires one swap. O(n) time, O(1) space."""
    nonzero = 0
    for value in nums:
        if value != 0:
            nonzero += 1
    answer = 0
    for index in range(nonzero):
        if nums[index] == 0:
            answer += 1
    return answer
