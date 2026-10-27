"""3831. Median of a Binary Search Tree Level
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(root, level).
Algorithm: Iterative breadth-first traversal; BST level order is value-sorted, so take the upper middle.
Complexity: O(n) time; O(maximum level width) auxiliary space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: solve(root, level), levelMedian, and Solution.levelMedian; root is a normal TreeNode with val/left/right, not an encoded list.
Specification: https://leetcode.com/problems/median-of-a-binary-search-tree-level/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3831.Median%20of%20a%20Binary%20Search%20Tree%20Level/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
"""

def solve(root, level):
    current = [] if root is None else [root]
    depth = 0
    while current and depth < level:
        following = []
        for node in current:
            if node.left is not None:
                following.append(node.left)
            if node.right is not None:
                following.append(node.right)
        current = following
        depth += 1
    # Left-to-right nodes on a BST level are already sorted by value.
    return current[len(current) // 2].val if current else -1


def levelMedian(root, level):
    return solve(root, level)


class Solution:
    def levelMedian(self, root, level):
        return solve(root, level)
