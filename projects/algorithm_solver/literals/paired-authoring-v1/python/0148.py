# External ListNode shape: val: int, next: ListNode | None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


def split_run(head, size: int):
    if head is None:
        return None
    for _ in range(1, size):
        if head.next is None:
            break
        head = head.next
    remainder = head.next
    head.next = None
    return remainder


def merge_after(tail, left, right):
    while left is not None and right is not None:
        if left.val <= right.val:
            tail.next = left
            left = left.next
        else:
            tail.next = right
            right = right.next
        tail = tail.next
    tail.next = left if left is not None else right
    while tail.next is not None:
        tail = tail.next
    return tail


class Solution:
    def sortList(self, head):
        length = 0
        current = head
        while current is not None:
            length += 1
            current = current.next

        sentinel = Link(head)
        run_size = 1
        while run_size < length:
            before = sentinel
            current = sentinel.next
            while current is not None:
                left = current
                right = split_run(left, run_size)
                current = split_run(right, run_size)
                before = merge_after(before, left, right)
            run_size *= 2
        return sentinel.next
