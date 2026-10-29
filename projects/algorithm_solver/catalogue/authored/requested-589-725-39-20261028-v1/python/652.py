"""Original LeetCode 652 candidate; qualification unknown."""

def solve(root):
    identities, counts, memo, out = {}, {}, {}, []
    stack = [(root, False)]
    while stack:
        node, visited = stack.pop()
        if node is None: continue
        if not visited:
            stack.extend([(node, True), (node.right, False), (node.left, False)])
            continue
        key = (node.val, memo.get(id(node.left), 0), memo.get(id(node.right), 0))
        if key not in identities: identities[key] = len(identities) + 1
        identity = identities[key]
        memo[id(node)] = identity
        counts[identity] = counts.get(identity, 0) + 1
        if counts[identity] == 2: out.append(node)
    return out


class Solution:
    def findDuplicateSubtrees(self, root):
        return solve(root)
