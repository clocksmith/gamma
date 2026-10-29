"""Original frontend 381 variant; qualification unknown."""


class RandomizedCollection:
    def __init__(self):
        self.vals = []
        self.pos = {}
        self._state = 0x9E3779B9

    def _randrange(self, n: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % n

    def insert(self, val: int) -> bool:
        bucket = self.pos.setdefault(val, [])
        is_new = len(bucket) == 0
        bucket.append(len(self.vals))
        self.vals.append([val, len(bucket) - 1])
        return is_new

    def remove(self, val: int) -> bool:
        bucket = self.pos.get(val)
        if not bucket:
            return False
        idx = bucket.pop()
        last_val, last_slot = self.vals.pop()
        if idx < len(self.vals):
            self.vals[idx] = [last_val, last_slot]
            self.pos[last_val][last_slot] = idx
        return True

    def getRandom(self) -> int:
        return self.vals[self._randrange(len(self.vals))][0]


def solve(operation_names, argument_lists):
    instance = RandomizedCollection()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "insert":
            out.append(instance.insert(args[0]))
        elif op == "remove":
            out.append(instance.remove(args[0]))
        elif op == "getRandom":
            out.append(instance.getRandom())
        else:
            raise ValueError("unknown operation")
    return out
