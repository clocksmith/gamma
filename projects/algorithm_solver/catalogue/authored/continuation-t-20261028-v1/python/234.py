class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def isPalindrome(self, head):
        if head is None or head.next is None:
            return True
        def reverse(node):
            previous = None
            while node is not None:
                following = node.next
                node.next = previous
                previous = node
                node = following
            return previous
        half, fast = head, head
        while fast.next is not None and fast.next.next is not None:
            half = half.next
            fast = fast.next.next
        second = reverse(half.next)
        half.next = second
        left, right = head, second
        equal = True
        while right is not None:
            if left.val != right.val:
                equal = False
            left, right = left.next, right.next
        half.next = reverse(second)
        return equal
