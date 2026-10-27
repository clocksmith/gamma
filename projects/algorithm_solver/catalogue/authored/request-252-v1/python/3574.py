from math import gcd


def solve(nums, k):
    twos = [(value & -value).bit_length() - 1 for value in nums]
    answer = 0
    for left in range(len(nums)):
        divisor = 0
        minimum_twos = 31
        minimum_count = 0
        for right in range(left, len(nums)):
            divisor = gcd(divisor, nums[right])
            if twos[right] < minimum_twos:
                minimum_twos, minimum_count = twos[right], 1
            elif twos[right] == minimum_twos:
                minimum_count += 1
            # Only the factor two can improve, and every minimum-valuation item must double.
            multiplier = 2 if minimum_count <= k else 1
            answer = max(answer, divisor * multiplier * (right - left + 1))
    return answer
