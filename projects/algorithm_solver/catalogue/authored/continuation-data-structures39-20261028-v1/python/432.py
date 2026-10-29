"""Original frontend 432 variant; qualification unknown."""


class _Bucket:
    def __init__(self, count: int):
        self.count = count
        self.keys = set()
        self.prev = None
        self.next = None


class AllOne:
    def __init__(self):
        self.head = _Bucket(0)
        self.tail = _Bucket(0)
        self.head.next = self.tail
        self.tail.prev = self.head
        self.key_bucket = {}

    def _insert_after(self, node: _Bucket, new_node: _Bucket) -> _Bucket:
        nxt = node.next
        node.next = new_node
        new_node.prev = node
        new_node.next = nxt
        nxt.prev = new_node
        return new_node

    def _remove(self, node: _Bucket) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def inc(self, key: str) -> None:
        if key not in self.key_bucket:
            first = self.head.next
            if first is self.tail or first.count != 1:
                first = self._insert_after(self.head, _Bucket(1))
            first.keys.add(key)
            self.key_bucket[key] = first
        else:
            cur = self.key_bucket[key]
            nxt = cur.next
            if nxt is self.tail or nxt.count != cur.count + 1:
                nxt = self._insert_after(cur, _Bucket(cur.count + 1))
            nxt.keys.add(key)
            self.key_bucket[key] = nxt
            cur.keys.remove(key)
            if not cur.keys:
                self._remove(cur)

    def dec(self, key: str) -> None:
        cur = self.key_bucket[key]
        if cur.count == 1:
            del self.key_bucket[key]
        else:
            prv = cur.prev
            if prv is self.head or prv.count != cur.count - 1:
                prv = self._insert_after(cur.prev, _Bucket(cur.count - 1))
            prv.keys.add(key)
            self.key_bucket[key] = prv
        cur.keys.remove(key)
        if not cur.keys:
            self._remove(cur)

    def getMaxKey(self) -> str:
        if self.tail.prev is self.head:
            return ""
        return min(self.tail.prev.keys)

    def getMinKey(self) -> str:
        if self.head.next is self.tail:
            return ""
        return min(self.head.next.keys)


def solve(operation_names, argument_lists):
    instance = AllOne()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "inc":
            instance.inc(args[0])
            out.append(None)
        elif op == "dec":
            instance.dec(args[0])
            out.append(None)
        elif op == "getMaxKey":
            out.append(instance.getMaxKey())
        elif op == "getMinKey":
            out.append(instance.getMinKey())
        else:
            raise ValueError("unknown operation")
    return out
