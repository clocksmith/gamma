"""501. Find Mode in Binary Search Tree. Count equal runs in sorted inorder traversal without modifying the tree."""

def solve(root):
    stack = []
    node = root
    previous = None
    run = maximum = 0
    answer = []
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        run = run + 1 if node.val == previous else 1
        previous = node.val
        if run > maximum:
            maximum = run
            answer = [node.val]
        elif run == maximum:
            answer.append(node.val)
        node = node.right
    return answer


class Solution:
    def findMode(self, root):
        return solve(root)
