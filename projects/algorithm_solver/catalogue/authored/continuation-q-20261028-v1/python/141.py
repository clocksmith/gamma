"""Original frontend 141 source-defined native ABI; qualification unknown."""

class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None

def solve(head):
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False


class Solution:
    def hasCycle(self, head):
        return solve(head)
