"""Original frontend 138 source-defined native ABI; qualification unknown."""

class Node:
    def __init__(self, x, next=None, random=None):
        self.val = int(x)
        self.next = next
        self.random = random

def solve(head):
    clones = {None: None}
    current = head
    while current is not None:
        clones[current] = Node(current.val)
        current = current.next
    current = head
    while current is not None:
        clones[current].next = clones[current.next]
        clones[current].random = clones[current.random]
        current = current.next
    return clones[head]


class Solution:
    def copyRandomList(self, head):
        return solve(head)
