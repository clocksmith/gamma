"""297. Serialize and Deserialize Binary Tree."""
from __future__ import annotations
from collections import deque

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Codec:
    def serialize(self, root: TreeNode | None) -> str:
        values = []
        queue = deque([root])
        while queue:
            node = queue.popleft()
            if node is None:
                values.append('#')
            else:
                values.append(str(node.val))
                queue.append(node.left)
                queue.append(node.right)
        while values and values[-1] == '#':
            values.pop()
        return ','.join(values)

    def deserialize(self, data: str) -> TreeNode | None:
        if not data:
            return None
        values = data.split(',')
        root = TreeNode(int(values[0]))
        queue = deque([root])
        index = 1
        while queue and index < len(values):
            node = queue.popleft()
            if values[index] != '#':
                node.left = TreeNode(int(values[index]))
                queue.append(node.left)
            index += 1
            if index < len(values) and values[index] != '#':
                node.right = TreeNode(int(values[index]))
                queue.append(node.right)
            index += 1
        return root

def solve(root):
    codec = Codec()
    return codec.deserialize(codec.serialize(root))
