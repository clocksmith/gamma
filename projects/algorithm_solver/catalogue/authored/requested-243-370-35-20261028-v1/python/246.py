"""Original frontend 246 variant; qualification unknown."""


def solve(num: str) -> bool:
    mp = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    l, r = 0, len(num) - 1
    while l <= r:
        if num[l] not in mp or mp[num[l]] != num[r]:
            return False
        l += 1
        r -= 1
    return True


isStrobogrammatic = solve


class Solution:
    def isStrobogrammatic(self, num: str) -> bool:
        return solve(num)
