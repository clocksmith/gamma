"""Hack2Hire 68a4bbf8c11d63d6052ea308 (Design Worker Management System, variant 2 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class WorkerManagementSystem:
    def __init__(self):
        self.workers = {}

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
            w['open'] = (timestamp, w['comp'])
        else:
            start, comp = w['open']
            w['open'] = None
            w['total'] += timestamp - start
            w['stint'] += timestamp - start
        return 'registered'

    def get(self, workerId):
        w = self.workers.get(workerId)
        return -1 if w is None else w['total']

    def topNWorkers(self, n, position):
        ranked = sorted((-w['stint'], wid) for wid, w in self.workers.items() if w['pos'] == position)
        return ', '.join('%s(%d)' % (wid, -neg) for neg, wid in ranked[:n])


def solve(operation_names, argument_lists):
    if operation_names[0] != 'WorkerManagementSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = WorkerManagementSystem(*argument_lists[0])
    allowed = {'addWorker', 'registerWorker', 'get', 'topNWorkers'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
