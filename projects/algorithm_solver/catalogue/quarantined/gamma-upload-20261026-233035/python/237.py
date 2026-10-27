"""237. Delete Node in a Linked List."""
from __future__ import annotations

class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def solve(node: ListNode) -> None:
    node.val = node.next.val
    node.next = node.next.next

class Solution:
    def deleteNode(self, node) -> None:
        solve(node)
