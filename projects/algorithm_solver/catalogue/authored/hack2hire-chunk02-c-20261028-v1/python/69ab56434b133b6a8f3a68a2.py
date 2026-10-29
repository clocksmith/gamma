"""Hack2Hire 69ab56434b133b6a8f3a68a2 (Crypto Block Mining, variant 3) over an INFERRED spec; qualification unknown."""

def solve(transactions, blockSize):
    index = {row[0]: i for i, row in enumerate(transactions)}
    children = [[] for _ in transactions]
    roots = []
    for i, row in enumerate(transactions):
        (roots if row[3] is None else children[index[row[3]]]).append(i)
    order, subtree_end = [], {}
    stack = [(node, False) for node in reversed(roots)]
    while stack:  # iterative preorder recording where each subtree ends
        node, done = stack.pop()
        if done:
            subtree_end[node] = len(order)
            continue
        order.append(node)
        stack.append((node, True))
        stack.extend((child, False) for child in reversed(children[node]))
    n = len(order)
    best = [[0] * (blockSize + 1) for _ in range(n + 1)]
    for position in range(n - 1, -1, -1):
        node = order[position]
        size, fee = transactions[node][1], transactions[node][2]
        skip, take, here = best[subtree_end[node]], best[position + 1], best[position]
        for capacity in range(blockSize + 1):
            value = skip[capacity]
            if size <= capacity and take[capacity - size] + fee > value:
                value = take[capacity - size] + fee
            here[capacity] = value
    return best[0][blockSize]


class Solution:
    def maxFeesWithDependencies(self, transactions, blockSize):
        return solve(transactions, blockSize)
