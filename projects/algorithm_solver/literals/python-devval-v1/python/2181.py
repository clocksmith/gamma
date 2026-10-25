class ListNode:
    def __init__(self, value=0, next_node=None):
        self.val = value
        self.next = next_node


def solve(head):
    sentinel = ListNode()
    tail = sentinel
    current = head.next if head is not None else None
    total = 0
    while current is not None:
        if current.val == 0:
            tail.next = ListNode(total)
            tail = tail.next
            total = 0
        else:
            total += current.val
        current = current.next
    return sentinel.next
