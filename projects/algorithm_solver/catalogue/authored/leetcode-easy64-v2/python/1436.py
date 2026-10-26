"""1436. Destination City (Easy).

Specification: https://leetcode.com/problems/destination-city/description/
"""


def solve(paths: list[list[str]]) -> str:
    """O(n) expected set operations, O(n) space; preserve paths and its rows."""
    departures = {path[0] for path in paths}
    for path in paths:
        if path[1] not in departures:
            return path[1]
    return ''


class Solution:
    def destCity(self, paths: list[list[str]]) -> str:
        return solve(paths)
