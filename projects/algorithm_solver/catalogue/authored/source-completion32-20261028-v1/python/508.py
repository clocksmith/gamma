# 508 — Most Frequent Subtree Sum. Original implementation; authored candidate, not independently qualified.
def solve(root):
    sums, counts, stack = {}, {}, [(root, False)]
    while stack:
        node, visited = stack.pop()
        if node is None:
            continue
        if not visited:
            stack.extend(((node, True), (node.right, False), (node.left, False)))
        else:
            value = node.val + sums.get(id(node.left), 0) + sums.get(id(node.right), 0)
            sums[id(node)] = value
            counts[value] = counts.get(value, 0) + 1
    maximum = max(counts.values(), default=0)
    return [value for value, count in counts.items() if count == maximum]

findFrequentTreeSum = solve

class Solution:
    findFrequentTreeSum = staticmethod(solve)
