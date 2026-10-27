"""445. Add Two Numbers II. Add from digit stacks; never reverse or mutate either input list."""

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def solve(l1, l2):
    a, b = [], []
    node = l1
    while node:
        a.append(node.val)
        node = node.next
    node = l2
    while node:
        b.append(node.val)
        node = node.next
    head = None
    carry = 0
    while a or b or carry:
        total = carry + (a.pop() if a else 0) + (b.pop() if b else 0)
        carry, digit = divmod(total, 10)
        head = ListNode(digit, head)
    return head


class Solution:
    def addTwoNumbers(self, l1, l2):
        return solve(l1, l2)
