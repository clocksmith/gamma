"""1733. Minimum Number of People to Teach: teach one language only to endpoints of friendships lacking a shared language."""


def solve(n: int, languages: list[list[int]], friendships: list[list[int]]) -> int:
    """O(L + f * n) expected time and O(L + m + n) space, with L known-language entries, m users and f friendships; inputs are read-only."""
    known = [set(values) for values in languages]
    affected = set()
    for left, right in friendships:
        left -= 1
        right -= 1
        if known[left].isdisjoint(known[right]):
            affected.add(left)
            affected.add(right)
    counts = [0] * (n + 1)
    for person in affected:
        for language in known[person]:
            counts[language] += 1
    return len(affected) - max(counts)


class Solution:
    def minimumTeachings(self, n: int, languages: list[list[int]], friendships: list[list[int]]) -> int:
        return solve(n, languages, friendships)
