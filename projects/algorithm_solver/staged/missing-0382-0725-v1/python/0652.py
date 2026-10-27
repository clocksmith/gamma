"""652. Find Duplicate Subtrees. Intern subtree identities and return one original node per duplicated structure."""

def solve(root):
    identities, node_ids, counts = {}, {}, {}
    answer = []
    stack = [(root, False)] if root else []
    while stack:
        node, ready = stack.pop()
        if not ready:
            stack.append((node, True))
            if node.right:
                stack.append((node.right, False))
            if node.left:
                stack.append((node.left, False))
            continue
        signature = (node.val, node_ids.get(id(node.left), 0), node_ids.get(id(node.right), 0))
        if signature not in identities:
            identities[signature] = len(identities) + 1
        identifier = identities[signature]
        node_ids[id(node)] = identifier
        counts[identifier] = counts.get(identifier, 0) + 1
        if counts[identifier] == 2:
            answer.append(node)
    return answer


class Solution:
    def findDuplicateSubtrees(self, root):
        return solve(root)
