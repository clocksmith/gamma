"""Original frontend 369 variant; qualification unknown."""


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


plusOne = solve


class Solution:
    def plusOne(self, head):
        return solve(head)
