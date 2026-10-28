"""Original frontend 3906 variant; qualification unknown."""

def solve(l, r, directions):
    from functools import lru_cache
    visited = {0}
    position = 0
    for step in directions:
        position += 4 if step == 'D' else 1
        visited.add(position)
    def prefix(limit):
        if limit <= 0:
            return 0
        digits = tuple(map(int, str(limit).zfill(16)))
        @lru_cache(None)
        def count(index, previous, tight):
            if index == 16:
                return 1
            bound = digits[index] if tight else 9
            start = previous if index in visited else 0
            return sum(count(index + 1, digit if index in visited else previous, tight and digit == bound) for digit in range(start, bound + 1))
        return count(0, 0, True) - 1
    return prefix(r) - prefix(l - 1)


class Solution:
    def countGoodIntegersOnPath(self, l, r, directions):
        return solve(l, r, directions)
