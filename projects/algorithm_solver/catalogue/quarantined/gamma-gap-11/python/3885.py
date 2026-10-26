"""3885. Design Event Manager.

O((n+q) log(n+q)) total time and O(n+q) storage; versioned lazy heap prioritizes the smallest ID on equal priority.
"""
from __future__ import annotations
from heapq import heappop, heappush


class EventManager:
    def __init__(self, events: list[list[int]]):
        self.current = {}
        self.heap = []
        self.version = 0
        for event, priority in events:
            self.updatePriority(event, priority)

    def updatePriority(self, eventId: int, newPriority: int) -> None:
        self.version += 1
        self.current[eventId] = (newPriority, self.version)
        heappush(self.heap, (-newPriority, eventId, self.version))

    def pollHighest(self) -> int:
        while self.heap:
            negative_priority, event, version = heappop(self.heap)
            if self.current.get(event) == (-negative_priority, version):
                del self.current[event]
                return event
        return -1


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native interface with one request-local instance."""
    if not operations:
        return []
    instance = EventManager(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = EventManager
