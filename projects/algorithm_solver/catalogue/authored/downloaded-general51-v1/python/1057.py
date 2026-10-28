"""1057. Campus Bikes (Medium).

Specification: https://leetcode.com/problems/campus-bikes/description/
"""


def solve(workers: list[list[int]], bikes: list[list[int]]) -> list[int]:
    pairs = []
    for w, worker in enumerate(workers):
        for b, bike in enumerate(bikes):
            distance = abs(worker[0] - bike[0]) + abs(worker[1] - bike[1])
            pairs.append((distance, w, b))
    pairs.sort()
    answer = [-1] * len(workers)
    used_bikes = set()
    for _distance, w, b in pairs:
        if answer[w] == -1 and b not in used_bikes:
            answer[w] = b
            used_bikes.add(b)
    return answer


class Solution:
    def assignBikes(self, workers: list[list[int]], bikes: list[list[int]]) -> list[int]:
        return solve(workers, bikes)
