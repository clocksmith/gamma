def solve(nums: list[int], k: int) -> int:
    """Scan prefix maxima against suffix minima. O(n) time and space."""
    length = len(nums)
    suffix_minimum = [0] * length
    minimum = nums[-1]
    for index in range(length - 1, -1, -1):
        minimum = min(minimum, nums[index])
        suffix_minimum[index] = minimum
    maximum = nums[0]
    for index in range(length):
        maximum = max(maximum, nums[index])
        if maximum - suffix_minimum[index] <= k:
            return index
    return -1
