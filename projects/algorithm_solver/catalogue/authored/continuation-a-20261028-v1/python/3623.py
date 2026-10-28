from collections import Counter

def solve(points):
    counts = Counter(y for x, y in points)
    total = previous = 0
    for count in counts.values():
        pairs = count * (count - 1) // 2
        total = (total + previous * pairs) % 1000000007
        previous = (previous + pairs) % 1000000007
    return total


class Solution:
    def countTrapezoids(self, points):
        return solve(points)
