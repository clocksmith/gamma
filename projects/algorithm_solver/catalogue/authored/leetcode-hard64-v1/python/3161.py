"""3161. Block Placement Queries: obstacle ranks with a Fenwick tree and prefix maximum gaps."""


def solve(queries: list[list[int]]) -> list[bool]:
    """O(q log M + M) time and O(M + q) space, M=max queried coordinate + 1. Inputs are preserved."""
    limit = max(query[1] for query in queries) + 1
    bit = [0] * (limit + 2)
    size = 1
    while size < limit + 1:
        size *= 2
    gaps = [0] * (2 * size)

    def add(position):
        index = position + 1
        while index < len(bit):
            bit[index] += 1
            index += index & -index

    def prefix_count(end):
        total = 0
        while end:
            total += bit[end]
            end -= end & -end
        return total

    def kth(rank):
        index = 0
        step = 1 << ((len(bit) - 1).bit_length() - 1)
        while step:
            following = index + step
            if following < len(bit) and bit[following] < rank:
                rank -= bit[following]
                index = following
            step //= 2
        return index

    def update(position, length):
        index = position + size
        gaps[index] = length
        index //= 2
        while index:
            gaps[index] = max(gaps[2 * index], gaps[2 * index + 1])
            index //= 2

    def prefix_max(end):
        left = size
        right = size + end
        result = 0
        while left < right:
            if left & 1:
                result = max(result, gaps[left])
                left += 1
            if right & 1:
                right -= 1
                result = max(result, gaps[right])
            left //= 2
            right //= 2
        return result

    add(0)
    add(limit)
    update(limit, limit)
    answer = []
    for query in queries:
        position = query[1]
        rank = prefix_count(position + 1)
        previous = kth(rank)
        if query[0] == 1:
            following = kth(rank + 1)
            update(position, position - previous)
            update(following, following - position)
            add(position)
        else:
            available = max(prefix_max(position + 1), position - previous)
            answer.append(available >= query[2])
    return answer


class Solution:
    def getResults(self, queries: list[list[int]]) -> list[bool]:
        return solve(queries)
