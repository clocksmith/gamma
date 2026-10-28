"""Original frontend 3855 variant; qualification unknown."""

def solve(l, r, k):
    modulus = 10**9 + 7
    digit_sum = (l + r) * (r - l + 1) // 2
    repunit = (pow(10, k, modulus) - 1) * pow(9, -1, modulus) % modulus
    return digit_sum * pow(r - l + 1, k - 1, modulus) * repunit % modulus


class Solution:
    def sumOfNumbers(self, l, r, k):
        return solve(l, r, k)
