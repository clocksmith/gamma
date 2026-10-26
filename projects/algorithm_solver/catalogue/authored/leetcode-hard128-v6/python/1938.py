"""1938. Maximum Genetic Difference Query.

Maintain a counted binary trie along an iterative ancestor traversal; O((n+q)*B) time and space. Inputs are preserved.
"""

def solve(parents: list[int], queries: list[list[int]]) -> list[int]:
    n = len(parents)
    children = [[] for _ in parents]
    root = 0
    for node, parent in enumerate(parents):
        if parent == -1:
            root = node
        else:
            children[parent].append(node)
    attached = [[] for _ in parents]
    maximum = n - 1
    for index, (node, value) in enumerate(queries):
        attached[node].append((value, index))
        maximum = max(maximum, value)
    bits = max(1, maximum.bit_length())
    branch = [[-1, -1]]
    count = [0]

    def update(value, change):
        state = 0
        count[state] += change
        for bit in range(bits - 1, -1, -1):
            digit = value >> bit & 1
            if branch[state][digit] == -1:
                branch[state][digit] = len(branch)
                branch.append([-1, -1])
                count.append(0)
            state = branch[state][digit]
            count[state] += change

    answer = [0] * len(queries)
    stack = [(root, False)]
    while stack:
        node, leaving = stack.pop()
        if leaving:
            update(node, -1)
            continue
        update(node, 1)
        for value, index in attached[node]:
            state = score = 0
            for bit in range(bits - 1, -1, -1):
                digit = value >> bit & 1
                opposite = branch[state][digit ^ 1]
                if opposite != -1 and count[opposite] > 0:
                    score |= 1 << bit
                    state = opposite
                else:
                    state = branch[state][digit]
            answer[index] = score
        stack.append((node, True))
        stack.extend((child, False) for child in reversed(children[node]))
    return answer


class Solution:
    def maxGeneticDifference(self, parents: list[int], queries: list[list[int]]) -> list[int]:
        return solve(parents, queries)
