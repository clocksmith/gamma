"""3879. Maximum Distinct Path Sum in a Binary Tree
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(root).
Algorithm: Convert to undirected adjacency, then iterative backtracking from each possible endpoint with a path-local distinct-value set.
Complexity: O(n^2) time; O(n) auxiliary space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: solve(root), maxSum, and Solution.maxSum; normal TreeNode objects.
Specification: https://leetcode.com/problems/maximum-distinct-path-sum-in-a-binary-tree/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3879.Maximum%20Distinct%20Path%20Sum%20in%20a%20Binary%20Tree/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Paths may turn through any ancestor and need not include the root. Negative totals are not pruned; all-negative trees return a nonempty path maximum.
"""

def solve(root):
    if root is None:
        raise ValueError("The specified tree is nonempty.")
    nodes = [root]
    adjacency = [[]]
    values = []
    for index, node in enumerate(nodes):
        values.append(node.val)
        for child in (node.left, node.right):
            if child is not None:
                child_index = len(nodes)
                nodes.append(child)
                adjacency.append([index])
                adjacency[index].append(child_index)
    answer = max(values)
    for start in range(len(nodes)):
        used_values = set()
        stack = [(start, -1, 0, False)]
        while stack:
            node, parent, total, leaving = stack.pop()
            value = values[node]
            if leaving:
                used_values.remove(value)
                continue
            if value in used_values:
                continue
            used_values.add(value)
            total += value
            answer = max(answer, total)
            stack.append((node, parent, total, True))
            for neighbor in adjacency[node]:
                if neighbor != parent:
                    stack.append((neighbor, node, total, False))
    return answer


def maxSum(root):
    return solve(root)


class Solution:
    def maxSum(self, root):
        return solve(root)
