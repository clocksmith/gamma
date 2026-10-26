"""3829. Design Ride Sharing System.

O(Q) expected total time and O(Q) storage for Q calls; FIFO matching with lazy cancellation.
"""
from __future__ import annotations
from collections import deque


class RideSharingSystem:
    def __init__(self):
        self.riders = deque()
        self.drivers = deque()
        self.waiting = set()

    def addRider(self, riderId: int) -> None:
        self.riders.append(riderId)
        self.waiting.add(riderId)

    def addDriver(self, driverId: int) -> None:
        self.drivers.append(driverId)

    def matchDriverWithRider(self) -> list[int]:
        while self.riders and self.riders[0] not in self.waiting:
            self.riders.popleft()
        if not self.drivers or not self.riders:
            return [-1, -1]
        rider = self.riders.popleft()
        self.waiting.remove(rider)
        return [self.drivers.popleft(), rider]

    def cancelRider(self, riderId: int) -> None:
        self.waiting.discard(riderId)


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native interface with one request-local instance."""
    if not operations:
        return []
    instance = RideSharingSystem(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = RideSharingSystem
