"""Original frontend 380 variant; qualification unknown."""


class RandomizedSet:
    def __init__(self):
        self.vals = []
        self.pos = {}
        self._state = 0x9E3779B9

    def _randrange(self, n: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % n

    def insert(self, val: int) -> bool:
        if val in self.pos:
            return False
        self.pos[val] = len(self.vals)
        self.vals.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.pos:
            return False
        idx = self.pos.pop(val)
        last = self.vals.pop()
        if idx < len(self.vals):
            self.vals[idx] = last
            self.pos[last] = idx
        return True

    def getRandom(self) -> int:
        return self.vals[self._randrange(len(self.vals))]


def solve(operation_names, argument_lists):
    instance = RandomizedSet()
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
