"""707. Design Linked List."""

class _Node:
    def __init__(self, value=0):
        self.value = value
        self.previous = None
        self.next = None


class MyLinkedList:
    def __init__(self):
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.previous = self.head
        self.size = 0

    def _at(self, index):
        if index < self.size // 2:
            node = self.head.next
            for _ in range(index):
                node = node.next
        else:
            node = self.tail
            for _ in range(self.size - index):
                node = node.previous
        return node

    def get(self, index: int) -> int:
        return -1 if index < 0 or index >= self.size else self._at(index).value

    def addAtHead(self, val: int) -> None:
        self.addAtIndex(0, val)

    def addAtTail(self, val: int) -> None:
        self.addAtIndex(self.size, val)

    def addAtIndex(self, index: int, val: int) -> None:
        if index > self.size:
            return
        index = max(index, 0)
        following = self._at(index)
        previous = following.previous
        node = _Node(val)
        node.previous, node.next = previous, following
        previous.next = following.previous = node
        self.size += 1

    def deleteAtIndex(self, index: int) -> None:
        if index < 0 or index >= self.size:
            return
        node = self._at(index)
        node.previous.next = node.next
        node.next.previous = node.previous
        self.size -= 1


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = MyLinkedList(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = MyLinkedList
