"""Original LeetCode 725 candidate; qualification unknown."""

class ListNode:
    def __init__(self, val=0, next=None): self.val, self.next = val, next

def solve(head, k):
    length, node = 0, head
    while node is not None: length += 1; node = node.next
    base, extra = divmod(length, k)
    result, node = [], head
    for part in range(k):
        dummy = ListNode(); tail = dummy
        for _ in range(base + (part < extra)):
            tail.next = ListNode(node.val); tail = tail.next; node = node.next
        result.append(dummy.next)
    return result


class Solution:
    def splitListToParts(self, head, k):
        return solve(head, k)
