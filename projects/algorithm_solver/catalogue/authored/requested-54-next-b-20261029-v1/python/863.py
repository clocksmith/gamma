"""Original value-target TreeNode development candidate; qualification unknown."""
from collections import deque

def solve(root, target, k):
    adjacency = {}
    stack = [root]
    while stack:
        node = stack.pop()
        adjacency.setdefault(node.val,[])
        for child in (node.left,node.right):
            if child is not None:
                adjacency.setdefault(child.val,[]).append(node.val)
                adjacency[node.val].append(child.val)
                stack.append(child)
    queue = deque([(target,0)])
    seen = {target}
    result = []
    while queue:
        value,distance = queue.popleft()
        if distance == k:
            result.append(value)
            continue
        for neighbor in adjacency[value]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor,distance+1))
    return result

class Solution:
    def distanceK(self, root, target, k):
        return solve(root,target,k)
