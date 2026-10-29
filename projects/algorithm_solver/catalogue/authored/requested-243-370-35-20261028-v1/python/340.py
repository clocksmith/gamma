"""Original frontend 340 variant; qualification unknown."""


def solve(s: str, k: int) -> int:
    if k == 0:
        return 0
    cnt = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        cnt[ch] = cnt.get(ch, 0) + 1
        while len(cnt) > k:
            lch = s[left]
            cnt[lch] -= 1
            if cnt[lch] == 0:
                del cnt[lch]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


lengthOfLongestSubstringKDistinct = solve


class Solution:
    def lengthOfLongestSubstringKDistinct(self, s: str, k: int) -> int:
        return solve(s, k)
