from collections import Counter


def solve(nums):
    modulus = 1_000_000_007
    right = Counter(nums)
    left = Counter()
    answer = 0
    for value in nums:
        right[value] -= 1
        answer = (answer + left[value * 2] * right[value * 2]) % modulus
        left[value] += 1
    return answer
