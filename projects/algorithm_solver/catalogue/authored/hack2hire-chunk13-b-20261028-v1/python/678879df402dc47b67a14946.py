"""Hack2Hire 678879df402dc47b67a14946 (Search History System) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class _Node:
    __slots__ = ('term', 'prev', 'next')

    def __init__(self, term):
        self.term = term
        self.prev = self.next = None


class SearchHistory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.nodes = {}
        self.head = _Node(None)  # most recent side
        self.tail = _Node(None)  # least recent side
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def add(self, term):
        node = self.nodes.get(term)
        if node is not None:
            self._unlink(node)
        else:
            node = _Node(term)
            self.nodes[term] = node
        self._push_front(node)
        if len(self.nodes) > self.capacity:
            oldest = self.tail.prev
            self._unlink(oldest)
            del self.nodes[oldest.term]

    def getTopK(self, k):
        out = []
        node = self.head.next
        while node is not self.tail and len(out) < k:
            out.append(node.term)
            node = node.next
        return out


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SearchHistory' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = SearchHistory(*argument_lists[0])
    allowed = {'add', 'getTopK'}
    voids = {'add'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
