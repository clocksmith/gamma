"""876. Middle of the Linked List (Easy).

Specification: https://leetcode.com/problems/middle-of-the-linked-list/description/
"""


def solve(head):
    """O(n) time, O(1) space; return the original middle node without changing links."""
    slow = head
    fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
    return slow


class Solution:
    def middleNode(self, head):
        return solve(head)
