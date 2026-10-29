"""Original frontend 817 source-defined native ABI; qualification not qualified."""

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def solve(head, nums):
    members = set(nums)
    count = 0
    node = head
    while node is not None:
        if node.val in members and (node.next is None or node.next.val not in members):
            count += 1
        node = node.next
    return count


class Solution:
    def numComponents(self, head, nums):
        return solve(head, nums)
