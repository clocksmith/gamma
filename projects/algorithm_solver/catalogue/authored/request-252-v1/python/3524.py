def solve(nums, k):
    result = [0] * k
    endings = [0] * k
    for value in nums:
        remainder = value % k
        current = [0] * k
        current[remainder] = 1
        for previous, count in enumerate(endings):
            current[previous * remainder % k] += count
        for remainder, count in enumerate(current):
            result[remainder] += count
        endings = current
    return result
