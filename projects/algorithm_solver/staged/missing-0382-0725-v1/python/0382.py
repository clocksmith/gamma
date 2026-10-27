"""382. Linked List Random Node."""

from random import randrange


class Solution:
    """Reservoir sampling: O(n) per draw and O(1) auxiliary space; links are preserved."""
    def __init__(self, head):
        self.head = head

    def getRandom(self) -> int:
        node = self.head
        selected = None
        count = 0
        while node is not None:
            count += 1
            if randrange(count) == 0:
                selected = node.val
            node = node.next
        return selected


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = Solution(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
