"""1416. Restore The Array: prefix DP over bounded decimal values; O(n log(k+1)) time and O(n) space."""


def solve(s: str, k: int) -> int:
    modulus = 1_000_000_007
    ways = [0] * (len(s) + 1)
    ways[0] = 1
    for start in range(len(s)):
        if s[start] == '0' or ways[start] == 0:
            continue
        value = 0
        for end in range(start, len(s)):
            value = value * 10 + ord(s[end]) - ord('0')
            if value > k:
                break
            ways[end + 1] = (ways[end + 1] + ways[start]) % modulus
    return ways[-1]


class Solution:
    def numberOfArrays(self, s: str, k: int) -> int:
        return solve(s, k)
