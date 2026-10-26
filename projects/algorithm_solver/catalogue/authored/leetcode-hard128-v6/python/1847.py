"""1847. Closest Room.

Offline size sweep with Fenwick order statistics on room IDs; O((n+q) log n + q log q) time, O(n+q) space. Inputs are preserved.
"""

from bisect import bisect_left, bisect_right


def solve(rooms: list[list[int]], queries: list[list[int]]) -> list[int]:
    ids = sorted(room[0] for room in rooms)
    ordered = sorted(rooms, key=lambda room: -room[1])
    requests = sorted(enumerate(queries), key=lambda item: -item[1][1])
    tree = [0] * (len(ids) + 1)

    def prefix(index):
        total = 0
        while index:
            total += tree[index]
            index -= index & -index
        return total

    def select(order):
        index = 0
        step = 1 << (len(ids).bit_length() - 1)
        while step:
            following = index + step
            if following < len(tree) and tree[following] < order:
                order -= tree[following]
                index = following
            step //= 2
        return ids[index]

    answers = [-1] * len(queries)
    admitted = 0
    for query_index, (preferred, minimum_size) in requests:
        while admitted < len(ordered) and ordered[admitted][1] >= minimum_size:
            index = bisect_left(ids, ordered[admitted][0]) + 1
            while index < len(tree):
                tree[index] += 1
                index += index & -index
            admitted += 1
        if not admitted:
            continue
        before = prefix(bisect_right(ids, preferred))
        candidates = []
        if before:
            candidates.append(select(before))
        if before < admitted:
            candidates.append(select(before + 1))
        answers[query_index] = min(candidates, key=lambda value: (abs(value - preferred), value))
    return answers


class Solution:
    def closestRoom(self, rooms: list[list[int]], queries: list[list[int]]) -> list[int]:
        return solve(rooms, queries)
