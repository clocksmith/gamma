"""Original frontend 369 variant; qualification unknown."""

import copy


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def solve(head):
    if isinstance(head, list):
        arr = list(head)
        for i in range(len(arr) - 1, -1, -1):
            if arr[i] < 9:
                arr[i] += 1
                return arr
            arr[i] = 0
        return [1] + arr
    return _plus_one_in_place(_clone_list(head))


def _clone_list(head):
    """Copy a caller's linked list; reject a node reached twice (cycle). copy.copy keeps the caller's class."""
    seen = set()
    sentinel = ListNode()
    tail = sentinel
    cur = head
    while cur is not None:
        if id(cur) in seen:
            raise ValueError("plusOne: input list has a cycle")
        seen.add(id(cur))
        dup = copy.copy(cur)
        dup.next = None
        tail.next = dup
        tail = dup
        cur = cur.next
    return sentinel.next


def _plus_one_in_place(head):
    """Add one to the digits of a list the caller of this helper owns; may prepend one node."""
    sentinel = ListNode(0, head)
    not_nine = sentinel
    cur = head
    while cur is not None:
        if cur.val != 9:
            not_nine = cur
        cur = cur.next
    not_nine.val += 1
    cur = not_nine.next
    while cur is not None:
        cur.val = 0
        cur = cur.next
    return sentinel if sentinel.val else sentinel.next


def plusOne(head):
    """Official LeetCode ABI: increments the caller's list in place and returns its head.

    native_effects.mutates_inputs = true (a new head node is prepended when every digit is 9).
    A list of digits is handled by the pure path, so list callers see no mutation.
    """
    if isinstance(head, list):
        return solve(head)
    return _plus_one_in_place(head)


class Solution:
    def plusOne(self, head):
        return plusOne(head)
