"""1707. Maximum XOR With an Element From Array: offline limit sweep and binary trie; O(n log n+q log q+31*(n+q)) time and O(31*n+q) space."""

from array import array


def solve(nums: list[int], queries: list[list[int]]) -> list[int]:
    ordered = sorted(nums)
    pending = sorted((limit, value, index) for index, (value, limit) in enumerate(queries))
    zero, one = array('i', [-1]), array('i', [-1])

    def insert(value: int) -> None:
        node = 0
        for bit in range(30, -1, -1):
            children = one if value & (1 << bit) else zero
            if children[node] == -1:
                children[node] = len(zero)
                zero.append(-1)
                one.append(-1)
            node = children[node]

    answers = [-1] * len(queries)
    count = 0
    for limit, value, index in pending:
        while count < len(ordered) and ordered[count] <= limit:
            insert(ordered[count])
            count += 1
        if count == 0:
            continue
        node = answer = 0
        for bit in range(30, -1, -1):
            preferred, fallback = (zero, one) if value & (1 << bit) else (one, zero)
            if preferred[node] != -1:
                answer |= 1 << bit
                node = preferred[node]
            else:
                node = fallback[node]
        answers[index] = answer
    return answers


class Solution:
    def maximizeXor(self, nums: list[int], queries: list[list[int]]) -> list[int]:
        return solve(nums, queries)
