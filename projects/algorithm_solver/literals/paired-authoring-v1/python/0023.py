# External ListNode shape: val: int, next: ListNode | None.
class Link:
    def __init__(self, next_node=None):
        self.next = next_node


def merge_runs(left, right):
    sentinel = Link()
    tail = sentinel
    while left is not None and right is not None:
        if left.val <= right.val:
            tail.next = left
            left = left.next
        else:
            tail.next = right
            right = right.next
        tail = tail.next
    tail.next = left if left is not None else right
    return sentinel.next


class Solution:
    def mergeKLists(self, lists):
        runs = lists.copy()
        while len(runs) > 1:
            next_runs = []
            for index in range(0, len(runs), 2):
                left = runs[index]
                right = runs[index + 1] if index + 1 < len(runs) else None
                next_runs.append(merge_runs(left, right))
            runs = next_runs
        return runs[0] if runs else None
