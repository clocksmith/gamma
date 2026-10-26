"""1721. Swapping Nodes in a Linked List: copy the list before swapping the two selected values."""


class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next


def solve(head: "ListNode | None", k: int) -> "ListNode | None":
    """O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only."""
    dummy = ListNode()
    tail = dummy
    current = head
    length = 0
    while current is not None:
        tail.next = ListNode(current.val)
        tail = tail.next
        current = current.next
        length += 1
    first = second = dummy.next
    for _ in range(k - 1):
        first = first.next
    for _ in range(length - k):
        second = second.next
    first.val, second.val = second.val, first.val
    return dummy.next


class Solution:
    def swapNodes(self, head: "ListNode | None", k: int) -> "ListNode | None":
        return solve(head, k)
