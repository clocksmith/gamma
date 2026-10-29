"""Original frontend 430 variant; qualification unknown."""


class Node:
    def __init__(self, val, prev=None, next=None, child=None):
        self.val = val
        self.prev = prev
        self.next = next
        self.child = child


def _from_multilevel_list(arr):
    if not arr:
        return None
    n = len(arr)
    i = 0
    nodes = []
    while i < n and arr[i] is not None:
        nodes.append(Node(arr[i]))
        i += 1
    for j in range(len(nodes) - 1):
        nodes[j].next = nodes[j + 1]
        nodes[j + 1].prev = nodes[j]
    curr = nodes[0]
    i += 1
    while i < n:
        while i < n and arr[i] is None:
            curr = curr.next
            i += 1
        if i >= n:
            break
        chain = []
        while i < n and arr[i] is not None:
            chain.append(Node(arr[i]))
            i += 1
        for j in range(len(chain) - 1):
            chain[j].next = chain[j + 1]
            chain[j + 1].prev = chain[j]
        curr.child = chain[0]
        curr = chain[0]
        i += 1
    return nodes[0]


def _flatten_nodes(head):
    if head is None:
        return None
    dummy = Node(0, None, head, None)
    prev = dummy
    stack = [head]
    while stack:
        curr = stack.pop()
        prev.next = curr
        curr.prev = prev
        if curr.next is not None:
            stack.append(curr.next)
        if curr.child is not None:
            stack.append(curr.child)
            curr.child = None
        prev = curr
    dummy.next.prev = None
    return dummy.next


def solve(head):
    if isinstance(head, list):
        root = _from_multilevel_list(head)
        flat = _flatten_nodes(root)
        out = []
        cur = flat
        while cur is not None:
            out.append(cur.val)
            cur = cur.next
        return out
    return _flatten_nodes(head)


flatten = solve


class Solution:
    def flatten(self, head):
        return solve(head)
