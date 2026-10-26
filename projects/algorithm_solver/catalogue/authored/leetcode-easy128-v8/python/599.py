"""599. Minimum Index Sum of Two Lists (Easy).

Specification: https://leetcode.com/problems/minimum-index-sum-of-two-lists/description/
"""


def solve(list1: list[str], list2: list[str]) -> list[str]:
    """O(n + m) expected time, O(n) auxiliary space; return ties in list2 encounter order."""
    positions = {name: index for index, name in enumerate(list1)}
    smallest = float('inf')
    result = []
    for index, name in enumerate(list2):
        if name not in positions:
            continue
        total = index + positions[name]
        if total < smallest:
            smallest = total
            result = []
        if total == smallest:
            result.append(name)
    return result


class Solution:
    def findRestaurant(self, list1: list[str], list2: list[str]) -> list[str]:
        return solve(list1, list2)
