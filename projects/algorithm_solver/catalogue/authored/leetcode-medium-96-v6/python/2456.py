"""2456. Most Popular Video Creator: aggregate creator views and retain each creator's highest-view lexicographically first video."""


def solve(creators: list[str], ids: list[str], views: list[int]) -> list[list[str]]:
    """O(n L) expected time and O(n) auxiliary entries for maximum identifier length L; inputs are read-only."""
    totals = {}
    best_video = {}
    for creator, identifier, count in zip(creators, ids, views):
        totals[creator] = totals.get(creator, 0) + count
        previous = best_video.get(creator)
        if previous is None or count > previous[0] or (count == previous[0] and identifier < previous[1]):
            best_video[creator] = (count, identifier)
    maximum = max(totals.values())
    return [[creator, best_video[creator][1]] for creator, count in totals.items() if count == maximum]


class Solution:
    def mostPopularCreator(self, creators: list[str], ids: list[str], views: list[int]) -> list[list[str]]:
        return solve(creators, ids, views)
