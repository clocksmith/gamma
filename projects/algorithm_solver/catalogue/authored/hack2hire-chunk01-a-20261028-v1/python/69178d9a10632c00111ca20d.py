"""Hack2Hire 69178d9a10632c00111ca20d (Delivery Cost Calculate, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


def _money(scaled):
    """scaled = sum of rateCents * seconds; exact cents = scaled / 3600, rounded half-up."""
    cents = (2 * scaled + 3600) // 7200
    return '%d.%02d' % (cents // 100, cents % 100)


class DeliverySystem:
    def __init__(self):
        self.rates = {}
        self.total = 0

    def addDriver(self, driverId, hourlyRateCents):
        self.rates[driverId] = hourlyRateCents

    def addDelivery(self, driverId, startTime, endTime):
        scaled = self.rates[driverId] * (endTime - startTime)
        self.total += scaled

    def getTotalCost(self):
        return _money(self.total)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DeliverySystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = DeliverySystem(*argument_lists[0])
    allowed = ['addDriver', 'addDelivery', 'getTotalCost']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(value)
    return result
