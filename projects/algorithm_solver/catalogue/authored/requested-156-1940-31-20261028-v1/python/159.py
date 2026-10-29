"""Original frontend 159 variant; qualification unknown."""


def solve(s: str) -> int:
    cnt = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        cnt[ch] = cnt.get(ch, 0) + 1
        while len(cnt) > 2:
            lch = s[left]
            cnt[lch] -= 1
            if cnt[lch] == 0:
                del cnt[lch]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


lengthOfLongestSubstringTwoDistinct = solve


class Solution:
    def lengthOfLongestSubstringTwoDistinct(self, s: str) -> int:
        return solve(s)
