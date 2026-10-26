"""1494. Parallel Courses II: completed-course masks and feasible semester subsets; O(3^n+n*2^n) time and O(2^n) space."""


def solve(n: int, relations: list[list[int]], k: int) -> int:
    prerequisites = [0] * n
    for before, after in relations:
        prerequisites[after - 1] |= 1 << (before - 1)
    full = (1 << n) - 1
    best = [n + 1] * (full + 1)
    best[0] = 0
    for completed in range(full):
        if best[completed] > n:
            continue
        available = 0
        for course in range(n):
            if not completed & (1 << course) and prerequisites[course] & completed == prerequisites[course]:
                available |= 1 << course
        if available.bit_count() <= k:
            following = completed | available
            best[following] = min(best[following], best[completed] + 1)
        else:
            subset = available
            while subset:
                if subset.bit_count() == k:
                    following = completed | subset
                    best[following] = min(best[following], best[completed] + 1)
                subset = (subset - 1) & available
    return best[full]


class Solution:
    def minNumberOfSemesters(self, n: int, relations: list[list[int]], k: int) -> int:
        return solve(n, relations, k)
