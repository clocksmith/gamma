"""Native FIFO rides with lazy deletion of cancelled rider identities."""
from collections import deque


class RideSharingSystem:
    def __init__(self):
        self.riders = deque()
        self.drivers = deque()
        self.waiting = set()

    def addRider(self, riderId):
        self.riders.append(riderId)
        self.waiting.add(riderId)

    def addDriver(self, driverId):
        self.drivers.append(driverId)

    def matchDriverWithRider(self):
        while self.riders and self.riders[0] not in self.waiting:
            self.riders.popleft()
        if not self.riders or not self.drivers:
            return [-1, -1]
        rider = self.riders.popleft()
        self.waiting.remove(rider)
        return [self.drivers.popleft(), rider]

    def cancelRider(self, riderId):
        self.waiting.discard(riderId)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RideSharingSystem' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance = RideSharingSystem()
    result = [None]
    methods = {name: getattr(instance, name) for name in
               ('addRider', 'addDriver', 'matchDriverWithRider', 'cancelRider')}
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        result.append(methods[name](*arguments))
    return result
