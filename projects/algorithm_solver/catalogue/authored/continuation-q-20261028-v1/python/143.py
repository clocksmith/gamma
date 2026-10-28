"""Original frontend 143 source-defined native ABI; qualification unknown."""

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def solve(head):
    if head is None or head.next is None:
        return None
    slow = fast = head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    second = slow.next
    slow.next = None
    previous = None
    while second is not None:
        following = second.next
        second.next = previous
        previous, second = second, following
    first, second = head, previous
    while second is not None:
        first_next, second_next = first.next, second.next
        first.next = second
        second.next = first_next
        first, second = first_next, second_next
    return None


class Solution:
    def reorderList(self, head):
        return solve(head)
