"""2816. Double a Number Represented as a Linked List: propagate decimal carries backward and construct nonaliasing output nodes."""
from __future__ import annotations


class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next


def solve(head: ListNode | None) -> ListNode | None:
    """O(n) time and O(n) auxiliary space excluding returned nodes; inputs are read-only."""
    digits = []
    current = head
    while current is not None:
        digits.append(current.val)
        current = current.next
    result = None
    carry = 0
    for digit in reversed(digits):
        carry, value = divmod(2 * digit + carry, 10)
        result = ListNode(value, result)
    if carry:
        result = ListNode(carry, result)
    return result


class Solution:
    def doubleIt(self, head: ListNode | None) -> ListNode | None:
        return solve(head)
