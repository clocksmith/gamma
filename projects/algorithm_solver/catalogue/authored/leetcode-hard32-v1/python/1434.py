"""1434. Number of Ways to Wear Different Hats to Each Other."""

def solve(hats: list[list[int]]) -> int:
    """Assign hats one at a time: O(40*n*2^n) time, O(2^n + 40*n) space."""
    modulus = 1_000_000_007
    people = [[] for _ in range(41)]
    for person, choices in enumerate(hats):
        for hat in choices:
            people[hat].append(person)
    states = 1 << len(hats)
    ways = [0] * states
    ways[0] = 1
    for hat in range(1, 41):
        following = ways.copy()
        for mask, count in enumerate(ways):
            if count == 0:
                continue
            for person in people[hat]:
                bit = 1 << person
                if mask & bit == 0:
                    following[mask | bit] = (following[mask | bit] + count) % modulus
        ways = following
    return ways[-1]


class Solution:
    def numberWays(self, hats: list[list[int]]) -> int:
        return solve(hats)
