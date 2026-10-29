"""Hack2Hire 68a4bbfbc11d63d6052ea30a (Design Worker Management System, variant 4 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import bisect


class WorkerManagementSystem:
    def __init__(self):
        self.workers = {}
        self.periods = []
        self.merged = None

    def addWorker(self, workerId, position, compensation):
        if workerId in self.workers:
            return False
        self.workers[workerId] = {'pos': position, 'comp': compensation, 'open': None, 'total': 0, 'stint': 0,
                                  'pending': None, 'entries': [], 'exits': [], 'comps': []}
        return True

    def registerWorker(self, workerId, timestamp):
        w = self.workers.get(workerId)
        if w is None:
            return 'invalid_request'
        if w['open'] is None:
            p = w['pending']
            if p is not None and timestamp >= p[2]:
                w['pos'], w['comp'], w['pending'], w['stint'] = p[0], p[1], None, 0
            w['open'] = (timestamp, w['comp'])
        else:
            start, comp = w['open']
            w['open'] = None
            w['total'] += timestamp - start
            w['stint'] += timestamp - start
            w['entries'].append(start)
            w['exits'].append(timestamp)
            w['comps'].append(comp)
        return 'registered'

    def get(self, workerId):
        w = self.workers.get(workerId)
        return -1 if w is None else w['total']

    def topNWorkers(self, n, position):
        ranked = sorted((-w['stint'], wid) for wid, w in self.workers.items() if w['pos'] == position)
        return ', '.join('%s(%d)' % (wid, -neg) for neg, wid in ranked[:n])

    def promote(self, workerId, newPosition, newCompensation, startTimestamp):
        w = self.workers.get(workerId)
        if w is None or w['pending'] is not None:
            return 'invalid_request'
        w['pending'] = (newPosition, newCompensation, startTimestamp)
        return 'success'

    def setDoublePaid(self, startTimestamp, endTimestamp):
        self.periods.append((startTimestamp, endTimestamp))
        self.merged = None

    def _merged_periods(self):
        if self.merged is None:
            starts, ends, prefix = [], [], [0]
            for s, e in sorted(self.periods):
                if ends and s <= ends[-1]:
                    if e > ends[-1]:
                        prefix[-1] += e - ends[-1]
                        ends[-1] = e
                else:
                    starts.append(s)
                    ends.append(e)
                    prefix.append(prefix[-1] + e - s)
            self.merged = (starts, ends, prefix)
        return self.merged

    def calcSalary(self, workerId, startTimestamp, endTimestamp):
        w = self.workers.get(workerId)
        if w is None:
            return -1
        entries, exits, comps = w['entries'], w['exits'], w['comps']
        starts, ends, prefix = self._merged_periods()
        first = bisect.bisect_left

        def covered(x):  # merged double-pay length before x: intervals starting before x, via binary search
            j = first(starts, x)
            return 0 if j == 0 else prefix[j - 1] + min(x, ends[j - 1]) - starts[j - 1]

        total = 0
        i = bisect.bisect_right(exits, startTimestamp)
        while i < len(entries) and entries[i] < endTimestamp:
            a, b = max(entries[i], startTimestamp), min(exits[i], endTimestamp)
            if b > a:
                total += comps[i] * (b - a)
                total += comps[i] * (covered(b) - covered(a))
            i += 1
        return total


def solve(operation_names, argument_lists):
    if operation_names[0] != 'WorkerManagementSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = WorkerManagementSystem(*argument_lists[0])
    allowed = {'addWorker', 'registerWorker', 'get', 'topNWorkers', 'promote', 'calcSalary', 'setDoublePaid'}
    voids = {'setDoublePaid'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
