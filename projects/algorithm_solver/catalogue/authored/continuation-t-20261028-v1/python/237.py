class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None


class Solution:
    def deleteNode(self, node):
        successor = node.next
        node.val = successor.val
        node.next = successor.next
