"""Original frontend 572 variant; qualification unknown."""
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _from_level_list(arr):
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    q = deque([root])
    i = 1
    while q and i < len(arr):
        node = q.popleft()
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                q.append(node.left)
        if i < len(arr):
            v = arr[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                q.append(node.right)
    return root


def _preorder_tokens(root):
    tokens = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node is None:
            tokens.append("#")
        else:
            tokens.append(f"^{node.val}")
            stack.append(node.right)
            stack.append(node.left)
    return tokens


def solve(root, subRoot) -> bool:
    if isinstance(root, list):
        root = _from_level_list(root)
    if isinstance(subRoot, list):
        subRoot = _from_level_list(subRoot)
    text = _preorder_tokens(root)
    pat = _preorder_tokens(subRoot)
    m = len(pat)
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pat[i] != pat[j]:
            j = pi[j - 1]
        if pat[i] == pat[j]:
            j += 1
        pi[i] = j
    j = 0
    for tok in text:
        while j > 0 and tok != pat[j]:
            j = pi[j - 1]
        if tok == pat[j]:
            j += 1
            if j == m:
                return True
    return False


isSubtree = solve


class Solution:
    def isSubtree(self, root, subRoot) -> bool:
        return solve(root, subRoot)
