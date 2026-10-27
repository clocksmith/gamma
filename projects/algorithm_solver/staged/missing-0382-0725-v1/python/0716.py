"""716. Max Stack."""

class _Node:
    def __init__(self, value=0, serial=0):
        self.value = value
        self.serial = serial
        self.index = -1
        self.previous = None
        self.next = None


class MaxStack:
    """Doubly linked stack plus indexed max heap: O(1) top/peekMax, O(log n) updates."""
    def __init__(self):
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.previous = self.head
        self.heap = []
        self.serial = 0

    def _higher(self, a, b):
        return (a.value, a.serial) > (b.value, b.serial)

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.heap[i].index = i
        self.heap[j].index = j

    def _up(self, index):
        while index:
            parent = (index - 1) // 2
            if not self._higher(self.heap[index], self.heap[parent]):
                break
            self._swap(index, parent)
            index = parent

    def _down(self, index):
        while 2 * index + 1 < len(self.heap):
            child = 2 * index + 1
            if child + 1 < len(self.heap) and self._higher(self.heap[child + 1], self.heap[child]):
                child += 1
            if not self._higher(self.heap[child], self.heap[index]):
                break
            self._swap(index, child)
            index = child

    def _remove_heap(self, index):
        removed = self.heap[index]
        last = self.heap.pop()
        if index < len(self.heap):
            self.heap[index] = last
            last.index = index
            if index and self._higher(last, self.heap[(index - 1) // 2]):
                self._up(index)
            else:
                self._down(index)
        removed.index = -1
        return removed

    def _unlink(self, node):
        node.previous.next = node.next
        node.next.previous = node.previous

    def push(self, x: int) -> None:
        node = _Node(x, self.serial)
        self.serial += 1
        node.previous, node.next = self.tail.previous, self.tail
        self.tail.previous.next = node
        self.tail.previous = node
        node.index = len(self.heap)
        self.heap.append(node)
        self._up(node.index)

    def pop(self) -> int:
        node = self.tail.previous
        self._unlink(node)
        self._remove_heap(node.index)
        return node.value

    def top(self) -> int:
        return self.tail.previous.value

    def peekMax(self) -> int:
        return self.heap[0].value

    def popMax(self) -> int:
        node = self._remove_heap(0)
        self._unlink(node)
        return node.value


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = MaxStack(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = MaxStack
