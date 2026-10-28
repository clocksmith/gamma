"""825. Friends Of Appropriate Ages (Medium).

Specification: https://leetcode.com/problems/friends-of-appropriate-ages/description/
"""


def solve(ages: list[int]) -> int:
    freq = [0] * 121
    for age in ages:
        freq[age] += 1
    total = 0
    for a in range(1, 121):
        if freq[a] == 0:
            continue
        for b in range(1, 121):
            if freq[b] == 0:
                continue
            if b <= a / 2 + 7:
                continue
            if b > a:
                continue
            if b > 100 and a < 100:
                continue
            if a == b:
                total += freq[a] * (freq[a] - 1)
            else:
                total += freq[a] * freq[b]
    return total


class Solution:
    def numFriendRequests(self, ages: list[int]) -> int:
        return solve(ages)
