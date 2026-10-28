"""Native auction class; lazy priority entries are checked against live bids."""
from heapq import heappop, heappush


class AuctionSystem:
    def __init__(self):
        self.bids = {}
        self.heaps = {}

    def addBid(self, userId, itemId, bidAmount):
        self.bids.setdefault(itemId, {})[userId] = bidAmount
        heappush(self.heaps.setdefault(itemId, []), (-bidAmount, -userId))

    def updateBid(self, userId, itemId, newAmount):
        self.addBid(userId, itemId, newAmount)

    def removeBid(self, userId, itemId):
        del self.bids[itemId][userId]

    def getHighestBidder(self, itemId):
        heap = self.heaps.get(itemId, [])
        live = self.bids.get(itemId, {})
        while heap:
            negative_amount, negative_user = heap[0]
            if live.get(-negative_user) == -negative_amount:
                return -negative_user
            heappop(heap)
        return -1


def solve(operation_names, argument_lists):
    if operation_names[0] != 'AuctionSystem' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance = AuctionSystem()
    result = [None]
    methods = {name: getattr(instance, name) for name in
               ('addBid', 'updateBid', 'removeBid', 'getHighestBidder')}
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        result.append(methods[name](*arguments))
    return result
