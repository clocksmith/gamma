"""160. Intersection of Two Linked Lists."""
from __future__ import annotations

class ListNode:
    def __init__(self, x: int, next=None):
        self.val = x
        self.next = next

def solve(headA: ListNode | None, headB: ListNode | None) -> ListNode | None:
    left, right = headA, headB
    while left is not right:
        left = headB if left is None else left.next
        right = headA if right is None else right.next
    return left

class Solution:
    def getIntersectionNode(self, headA, headB):
        return solve(headA, headB)
