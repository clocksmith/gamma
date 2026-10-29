"""Original frontend 1367 variant; qualification unknown."""
from collections import deque


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _from_level(arr):
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    q = deque([root])
    i = 1
    while q and i < len(arr):
        n = q.popleft()
        if i < len(arr):
            v = arr[i]; i += 1
            if v is not None:
                n.left = TreeNode(v); q.append(n.left)
        if i < len(arr):
            v = arr[i]; i += 1
            if v is not None:
                n.right = TreeNode(v); q.append(n.right)
    return root


def solve(head, root) -> bool:
    if isinstance(head, list):
        pat = list(head)
    else:
        pat = []
        cur = head
        while cur is not None:
            pat.append(cur.val)
            cur = cur.next
    if isinstance(root, list):
        root = _from_level(root)
    m = len(pat)
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pat[i] != pat[j]:
            j = pi[j - 1]
        if pat[i] == pat[j]:
            j += 1
        pi[i] = j
    stack = [(root, 0)]
    while stack:
        node, k = stack.pop()
        if node is None:
            continue
        while k > 0 and node.val != pat[k]:
            k = pi[k - 1]
        if node.val == pat[k]:
            k += 1
            if k == m:
                return True
        stack.append((node.left, k))
        stack.append((node.right, k))
    return False


isSubPath = solve


class Solution:
    def isSubPath(self, head, root) -> bool:
        return solve(head, root)
