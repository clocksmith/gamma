"""Original frontend 1237 variant; qualification unknown."""


def _eval_fn(cf, x: int, y: int) -> int:
    if hasattr(cf, "f"):
        return cf.f(x, y)
    if callable(cf):
        return cf(x, y)
    fid = int(cf)
    if fid == 1: return x + y
    if fid == 2: return x * y
    if fid == 3: return x * x + y
    if fid == 4: return x + y * y
    if fid == 5: return x * x + y * y
    if fid == 6: return (x + y) * (x + y)
    if fid == 7: return x * x * x + y * y * y
    if fid == 8: return x * x * y
    return x * y * y


def solve(customfunction, z: int):
    res = []
    x, y = 1, 1000
    while x <= 1000 and y >= 1:
        val = _eval_fn(customfunction, x, y)
        if val == z:
            res.append([x, y])
            x += 1
            y -= 1
        elif val < z:
            x += 1
        else:
            y -= 1
    return res


findSolution = solve


class Solution:
    def findSolution(self, customfunction, z: int):
        return solve(customfunction, z)
