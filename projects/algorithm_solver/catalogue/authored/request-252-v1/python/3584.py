def solve(nums, m):
    if m == 1:
        return max(value * value for value in nums)
    minimum = maximum = nums[0]
    answer = float('-inf')
    for right in range(m - 1, len(nums)):
        value = nums[right - m + 1]
        minimum = min(minimum, value)
        maximum = max(maximum, value)
        answer = max(answer, nums[right] * minimum, nums[right] * maximum)
    return answer
