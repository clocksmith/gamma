from bisect import bisect_left, bisect_right
from collections import deque


class Router:
    """Online FIFO router. Timestamp indexes are compacted amortized linearly."""
    def __init__(self, memoryLimit):
        self.limit = memoryLimit
        self.queue = deque()
        self.present = set()
        self.destinations = {}

    def addPacket(self, source, destination, timestamp):
        packet = (source, destination, timestamp)
        if packet in self.present:
            return False
        if len(self.queue) == self.limit:
            self.forwardPacket()
        self.queue.append(packet)
        self.present.add(packet)
        if destination not in self.destinations:
            self.destinations[destination] = [[], 0]
        self.destinations[destination][0].append(timestamp)
        return True

    def forwardPacket(self):
        if not self.queue:
            return []
        packet = self.queue.popleft()
        self.present.remove(packet)
        destination = packet[1]
        times, head = self.destinations[destination]
        head += 1
        if head == len(times):
            del self.destinations[destination]
        elif head * 2 >= len(times):
            self.destinations[destination] = [times[head:], 0]
        else:
            self.destinations[destination][1] = head
        return list(packet)

    def getCount(self, destination, startTime, endTime):
        entry = self.destinations.get(destination)
        if entry is None:
            return 0
        times, head = entry
        return (bisect_right(times, endTime, head)
                - bisect_left(times, startTime, head))


def solve(operations, arguments):
    """Explicit constructor-first operation-tape adapter; native Router exported."""
    router = Router(*arguments[0])
    output = [None]
    for operation, args in zip(operations[1:], arguments[1:]):
        output.append(getattr(router, operation)(*args))
    return output
