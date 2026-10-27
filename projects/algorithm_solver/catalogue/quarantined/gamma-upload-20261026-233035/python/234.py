"""234. Palindrome Linked List."""
from __future__ import annotations

class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def reverse(head):
    previous = None
    while head is not None:
        following = head.next
        head.next = previous
        previous = head
        head = following
    return previous

def solve(head: ListNode | None) -> bool:
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
    second = reverse(slow)
    copy = second
    first = head
    answer = True
    while copy is not None:
        if first.val != copy.val:
            answer = False
            break
        first = first.next
        copy = copy.next
    reverse(second)
    return answer

class Solution:
    def isPalindrome(self, head):
        return solve(head)
