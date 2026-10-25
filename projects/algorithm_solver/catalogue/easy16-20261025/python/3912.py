def solve(nums: list[int]) -> list[int]:
    """Mark strict records from both ends. O(n) time and space."""
    length = len(nums)
    valid = [False] * length
    maximum = -1
    for index in range(length):
        if nums[index] > maximum:
            valid[index] = True
        maximum = max(maximum, nums[index])
    maximum = -1
    for index in range(length - 1, -1, -1):
        if nums[index] > maximum:
            valid[index] = True
        maximum = max(maximum, nums[index])
    return [nums[index] for index in range(length) if valid[index]]
