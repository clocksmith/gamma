class Link:
    def __init__(self, next_node=None):
        self.next = next_node


def solve(head, left, right):
    sentinel = Link(head)
    previous = sentinel
    for _ in range(left - 1):
        previous = previous.next
    tail = previous.next
    for _ in range(right - left):
        moved = tail.next
        tail.next = moved.next
        moved.next = previous.next
        previous.next = moved
    return sentinel.next
