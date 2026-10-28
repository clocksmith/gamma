"""Original frontend 133 source-defined native ABI; qualification unknown."""

class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []

def solve(node):
    if node is None:
        return None
    clones = {node: Node(node.val)}
    queue = [node]
    for original in queue:
        for neighbor in original.neighbors:
            if neighbor not in clones:
                clones[neighbor] = Node(neighbor.val)
                queue.append(neighbor)
            clones[original].neighbors.append(clones[neighbor])
    return clones[node]


class Solution:
    def cloneGraph(self, node):
        return solve(node)
