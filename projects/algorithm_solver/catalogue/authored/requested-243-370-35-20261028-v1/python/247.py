"""Original frontend 247 variant; qualification unknown."""


def solve(n: int):
    pairs = (("0", "0"), ("1", "1"), ("6", "9"), ("8", "8"), ("9", "6"))

    def build(rem: int, total: int):
        if rem == 0:
            return [""]
        if rem == 1:
            return ["0", "1", "8"]
        mids = build(rem - 2, total)
        res = []
        for s in mids:
            for a, b in pairs:
                if rem == total and a == "0":
                    continue
                res.append(a + s + b)
        return sorted(res)

    return build(n, n)


findStrobogrammatic = solve


class Solution:
    def findStrobogrammatic(self, n: int):
        return solve(n)
