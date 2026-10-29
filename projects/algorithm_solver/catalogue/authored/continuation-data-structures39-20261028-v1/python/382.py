"""Original frontend 382 variant; qualification unknown."""


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def __init__(self, head):
        if isinstance(head, list):
            self.vals = list(head)
        else:
            vals = []
            cur = head
            while cur is not None:
                vals.append(cur.val)
                cur = cur.next
            self.vals = vals
        self._state = 0x9E3779B9

    def _randrange(self, n: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % n

    def getRandom(self) -> int:
        return self.vals[self._randrange(len(self.vals))]


def solve(operation_names, argument_lists):
    instance = Solution(argument_lists[0][0])
    out = [None]
    for op in operation_names[1:]:
        if op == "getRandom":
            out.append(instance.getRandom())
        else:
            raise ValueError("unknown operation")
    return out
