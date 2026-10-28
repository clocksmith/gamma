"""Original frontend 3918 variant; qualification unknown."""

def solve(n):
    reversed_n = int(str(n)[::-1])
    left, right = min(n, reversed_n), max(n, reversed_n)
    prime = [True] * (right + 1)
    prime[0] = False
    if right >= 1:
        prime[1] = False
    for value in range(2, int(right**0.5) + 1):
        if prime[value]:
            for multiple in range(value * value, right + 1, value):
                prime[multiple] = False
    return sum(value for value in range(left, right + 1) if prime[value])


class Solution:
    def sumOfPrimesInRange(self, n):
        return solve(n)
