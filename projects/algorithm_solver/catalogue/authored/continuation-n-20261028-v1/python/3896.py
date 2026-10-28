"""Original frontend 3896 variant; qualification unknown."""

def solve(nums):
    limit = max(2, 2 * max(nums))
    prime = bytearray([1]) * (limit + 1)
    prime[0] = prime[1] = 0
    for value in range(2, int(limit**0.5) + 1):
        if prime[value]:
            for multiple in range(value * value, limit + 1, value):
                prime[multiple] = 0
    following = [0] * (limit + 1)
    next_prime = limit + 1
    for value in range(limit, -1, -1):
        if prime[value]:
            next_prime = value
        following[value] = next_prime
    answer = 0
    for i, value in enumerate(nums):
        if i % 2 == 0:
            answer += following[value] - value
        elif prime[value]:
            answer += 2 if value == 2 else 1
    return answer


class Solution:
    def minOperations(self, nums):
        return solve(nums)
