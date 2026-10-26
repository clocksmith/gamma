"""2007. Find Original Array From Doubled Array: pair each smallest remaining nonnegative value with its double."""


def solve(changed: list[int]) -> list[int]:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    if len(changed) % 2:
        return []
    counts = {}
    for value in changed:
        counts[value] = counts.get(value, 0) + 1
    answer = []
    for value in sorted(changed):
        if counts[value] == 0:
            continue
        counts[value] -= 1
        doubled = 2 * value
        if counts.get(doubled, 0) == 0:
            return []
        counts[doubled] -= 1
        answer.append(value)
    return answer


class Solution:
    def findOriginalArray(self, changed: list[int]) -> list[int]:
        return solve(changed)
