"""1282. Group the People Given the Group Size They Belong To: collect each requested size until a complete group is ready."""


def solve(groupSizes: list[int]) -> list[list[int]]:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    pending = {}
    result = []
    for person, size in enumerate(groupSizes):
        group = pending.setdefault(size, [])
        group.append(person)
        if len(group) == size:
            result.append(group)
            del pending[size]
    return result


class Solution:
    def groupThePeople(self, groupSizes: list[int]) -> list[list[int]]:
        return solve(groupSizes)
