"""Original frontend 3932 variant; qualification unknown."""

def solve(l, r, k):
    def floor_root(bound):
        if bound < 0:
            return -1
        low, high = 0, bound + 1
        def fits(base):
            value = 1
            for _ in range(k):
                if base and value > bound // base:
                    return False
                value *= base
            return value <= bound
        while low + 1 < high:
            middle = (low + high) // 2
            if fits(middle):
                low = middle
            else:
                high = middle
        return low
    return floor_root(r) - floor_root(l - 1)


class Solution:
    def countKthRoots(self, l, r, k):
        return solve(l, r, k)
