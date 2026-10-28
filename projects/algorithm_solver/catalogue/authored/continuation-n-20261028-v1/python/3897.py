"""Original frontend 3897 variant; qualification unknown."""

def solve(nums1, nums0):
    modulus = 10**9 + 7
    total = sum(nums1) + sum(nums0)
    powers = [1]
    for _ in range(total):
        powers.append(powers[-1] * 2 % modulus)
    def key(index):
        a, b = nums1[index], nums0[index]
        return (0, 0, 0) if b == 0 else (2, 0, 0) if a == 0 else (1, -a, b)
    answer = 0
    for i in sorted(range(len(nums1)), key=key):
        a, b = nums1[i], nums0[i]
        answer = (answer * powers[a + b] + (powers[a] - 1) * powers[b]) % modulus
    return answer


class Solution:
    def maxValue(self, nums1, nums0):
        return solve(nums1, nums0)
