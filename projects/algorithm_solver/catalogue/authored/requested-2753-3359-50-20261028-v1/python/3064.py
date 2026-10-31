"""Original frontend 3064 variant; qualification unknown."""


def solve(n: int = 0) -> int:
    if isinstance(n, int):
        ans = 0
        for b in range(30):
            if (n >> b) & 1:
                ans |= 1 << b
        return ans
    ans = 0
    for b in range(30):
        if n(1 << b) > 0:
            ans |= 1 << b
    return ans


findNumber = solve


class Solution:
    def findNumber(self, n=None) -> int:
        if n is not None:
            return solve(n)
        fn = globals().get("commonSetBits")
        return solve(fn) if fn is not None else 0
