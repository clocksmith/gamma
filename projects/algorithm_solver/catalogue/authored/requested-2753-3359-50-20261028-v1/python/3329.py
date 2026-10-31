"""Original frontend 3329 variant; qualification unknown."""


def solve(s: str, k: int) -> int:
    cnt = {}
    left = 0
    ans = 0
    n = len(s)
    for right, ch in enumerate(s):
        cnt[ch] = cnt.get(ch, 0) + 1
        while cnt[ch] >= k:
            ans += n - right
            lch = s[left]
            cnt[lch] -= 1
            left += 1
    return ans


numberOfSubstrings = solve


class Solution:
    def numberOfSubstrings(self, s: str, k: int) -> int:
        return solve(s, k)
