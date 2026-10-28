from collections import Counter


def solve(n):
    cubes = []
    x = 1
    while x * x * x <= n:
        cubes.append(x * x * x)
        x += 1
    counts = Counter()
    for i, a in enumerate(cubes):
        for j in range(i, len(cubes)):
            total = a + cubes[j]
            if total > n:
                break
            counts[total] += 1
    return sorted(value for value, count in counts.items() if count >= 2)


class Solution:
    def findGoodIntegers(self, n):
        return solve(n)
