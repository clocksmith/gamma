def solve(nums):
    single = sum(value for value in nums if value < 10)
    double = sum(value for value in nums if value >= 10)
    return single != double
