"""3624. Number of Integers With Popcount-Depth Equal to K II.

Maintain one Fenwick count tree per reduction depth, updating only a changed value classification; O((n+q) log n+(n+q) log V) time and O(n+q) space. Inputs are preserved.
"""

def solve(nums: list[int], queries: list[list[int]]) -> list[int]:
    n = len(nums)
    trees = [[0] * (n + 1) for _ in range(7)]

    def classify(value):
        depth = 0
        while value != 1:
            value = value.bit_count()
            depth += 1
        return depth

    def update(depth, index, difference):
        index += 1
        while index <= n:
            trees[depth][index] += difference
            index += index & -index

    def prefix(depth, end):
        answer = 0
        while end:
            answer += trees[depth][end]
            end -= end & -end
        return answer

    depths = [classify(value) for value in nums]
    for index, depth in enumerate(depths):
        update(depth, index, 1)
    answers = []
    for query in queries:
        if query[0] == 1:
            _, left, right, depth = query
            answers.append(prefix(depth, right + 1) - prefix(depth, left))
        else:
            _, index, value = query
            following = classify(value)
            update(depths[index], index, -1)
            update(following, index, 1)
            depths[index] = following
    return answers


class Solution:
    def popcountDepth(self, nums: list[int], queries: list[list[int]]) -> list[int]:
        return solve(nums, queries)
