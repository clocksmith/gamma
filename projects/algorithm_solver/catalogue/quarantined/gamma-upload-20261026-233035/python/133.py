"""133. Clone Graph."""
from __future__ import annotations
from collections import deque

class Node:
    def __init__(self, val: int = 0, neighbors=None):
        self.val = val
        self.neighbors = [] if neighbors is None else neighbors

def solve(node: Node | None) -> Node | None:
    if node is None:
        return None
    copies = {node: Node(node.val)}
    queue = deque([node])
    while queue:
        current = queue.popleft()
        for neighbor in current.neighbors:
            if neighbor not in copies:
                copies[neighbor] = Node(neighbor.val)
                queue.append(neighbor)
            copies[current].neighbors.append(copies[neighbor])
    return copies[node]

class Solution:
    def cloneGraph(self, node):
        return solve(node)
