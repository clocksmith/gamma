class ListNode:
    def __init__(self, val):
        self.val = val
        self.next = None


class Solution:
    def getIntersectionNode(self, headA, headB):
        first, second = headA, headB
        while first is not second:
            first = headB if first is None else first.next
            second = headA if second is None else second.next
        return first
