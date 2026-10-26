"""21. Merge Two Sorted Lists (Easy).

Specification: https://leetcode.com/problems/merge-two-sorted-lists/description/
"""


def solve(list1, list2):
    """O(n + m) time, O(1) space; splice the original disjoint nodes and preserve their values."""
    if list1 is None:
        return list2
    if list2 is None:
        return list1
    if list1.val <= list2.val:
        head = list1
        list1 = list1.next
    else:
        head = list2
        list2 = list2.next
    tail = head
    while list1 is not None and list2 is not None:
        if list1.val <= list2.val:
            tail.next = list1
            list1 = list1.next
        else:
            tail.next = list2
            list2 = list2.next
        tail = tail.next
    tail.next = list2 if list1 is None else list1
    return head


class Solution:
    def mergeTwoLists(self, list1, list2):
        return solve(list1, list2)
