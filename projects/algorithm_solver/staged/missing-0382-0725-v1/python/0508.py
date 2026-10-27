"""508. Most Frequent Subtree Sum. Postorder subtree sums; returned ties are sorted for deterministic cross-language output."""

from collections import Counter

def solve(root):
    if not root:
        return []
    sums, counts = {}, Counter()
    stack = [(root, False)]
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right:
                stack.append((node.right, False))
            if node.left:
                stack.append((node.left, False))
        else:
            total = node.val + sums.get(id(node.left), 0) + sums.get(id(node.right), 0)
            sums[id(node)] = total
            counts[total] += 1
    maximum = max(counts.values())
    return sorted(total for total, count in counts.items() if count == maximum)


class Solution:
    def findFrequentTreeSum(self, root):
        return solve(root)
