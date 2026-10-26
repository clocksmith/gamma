"""3815. Design Auction System.

O(Q log Q) total time and O(Q) storage over Q operations; versioned lazy heaps preserve updates and removals.
"""
from __future__ import annotations
from heapq import heappop, heappush


class AuctionSystem:
    def __init__(self):
        self.current = {}
        self.heaps = {}
        self.version = 0

    def addBid(self, userId: int, itemId: int, bidAmount: int) -> None:
        self.version += 1
        self.current.setdefault(itemId, {})[userId] = (bidAmount, self.version)
        heap = self.heaps.setdefault(itemId, [])
        heappush(heap, (-bidAmount, -userId, self.version))

    def updateBid(self, userId: int, itemId: int, newAmount: int) -> None:
        self.addBid(userId, itemId, newAmount)

    def removeBid(self, userId: int, itemId: int) -> None:
        del self.current[itemId][userId]

    def getHighestBidder(self, itemId: int) -> int:
        heap = self.heaps.get(itemId, [])
        current = self.current.get(itemId, {})
        while heap:
            negative_amount, negative_user, version = heap[0]
            user = -negative_user
            if current.get(user) == (-negative_amount, version):
                return user
            heappop(heap)
        return -1


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay the native interface with one request-local instance."""
    if not operations:
        return []
    instance = AuctionSystem(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = AuctionSystem
