"""Original frontend 1396 variant; qualification unknown."""


class UndergroundSystem:
    def __init__(self):
        self.cin = {}
        self.stats = {}

    def checkIn(self, id: int, stationName: str, t: int) -> None:
        self.cin[id] = (stationName, t)

    def checkOut(self, id: int, stationName: str, t: int) -> None:
        st, t0 = self.cin.pop(id)
        pair = self.stats.setdefault((st, stationName), [0, 0])
        pair[0] += t - t0
        pair[1] += 1

    def getAverageTime(self, startStation: str, endStation: str) -> float:
        tot, cnt = self.stats[(startStation, endStation)]
        return tot / float(cnt)


def solve(operation_names, argument_lists):
    inst = UndergroundSystem()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "checkIn":
            inst.checkIn(args[0], args[1], args[2])
            out.append(None)
        elif op == "checkOut":
            inst.checkOut(args[0], args[1], args[2])
            out.append(None)
        else:
            out.append(inst.getAverageTime(args[0], args[1]))
    return out
