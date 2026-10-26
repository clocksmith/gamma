"""1505. Minimum Possible Integer After at Most K Adjacent Swaps On Digits.

Greedily extract the smallest reachable digit using a Fenwick tree of removals; O(10*n*log n) time, O(n) space.
"""

def solve(num: str, k: int) -> str:
    n = len(num)
    positions = [[] for _ in range(10)]
    for index, char in enumerate(num):
        positions[int(char)].append(index)
    heads = [0] * 10
    removed = [0] * (n + 1)
    answer = []
    for _ in range(n):
        for digit in range(10):
            if heads[digit] == len(positions[digit]):
                continue
            position = positions[digit][heads[digit]]
            index = position + 1
            before = 0
            while index:
                before += removed[index]
                index -= index & -index
            cost = position - before
            if cost > k:
                continue
            k -= cost
            answer.append(str(digit))
            heads[digit] += 1
            index = position + 1
            while index <= n:
                removed[index] += 1
                index += index & -index
            break
    return ''.join(answer)


class Solution:
    def minInteger(self, num: str, k: int) -> str:
        return solve(num, k)
