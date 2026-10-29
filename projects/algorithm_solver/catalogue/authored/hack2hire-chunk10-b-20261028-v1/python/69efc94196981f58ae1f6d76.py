"""Hack2Hire 69efc94196981f58ae1f6d76 (Design a Task Assignment System, variant 3 of 4) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import heapq


class TaskManager:
    def __init__(self):
        self.tasks = {}  # taskId -> [name, priority, creation number]
        self.count = 0
        self.users = {}
        self.seq = 0

    def addTask(self, timestamp, name, priority):
        self.count += 1
        taskId = 'taskId%d' % self.count
        self.tasks[taskId] = [name, priority, self.count]
        return taskId

    def updateTask(self, timestamp, taskId, name, priority):
        task = self.tasks.get(taskId)
        if task is None:
            return False
        task[0], task[1] = name, priority
        return True

    def getTask(self, timestamp, taskId):
        task = self.tasks.get(taskId)
        return '' if task is None else '%s(%d)' % (task[0], task[1])

    def _ordered(self, nameFilter, limit):
        picked = sorted((-t[1], t[2], tid) for tid, t in self.tasks.items() if nameFilter is None or nameFilter in t[0])
        return [tid for _, _, tid in picked[:limit]]

    def searchTasks(self, timestamp, nameFilter, maxResults):
        return self._ordered(nameFilter, maxResults)

    def listTasksSorted(self, timestamp, limit):
        return self._ordered(None, limit)

    def _user(self, userId, now):
        user = self.users.get(userId)
        if user is not None:
            heap, active = user['heap'], user['active']
            while heap and heap[0][0] <= now:
                finish, seq, taskId = heapq.heappop(heap)
                entry = active.get(taskId)
                if entry is not None and entry[1] == seq:
                    del active[taskId]
                    user['overdue'].append((seq, taskId))
        return user

    def addUser(self, timestamp, userId, quota):
        if userId in self.users:
            return False
        self.users[userId] = {'quota': quota, 'active': {}, 'heap': [], 'overdue': []}
        return True

    def assignTask(self, timestamp, taskId, userId, finishTime):
        user = self._user(userId, timestamp)
        if user is None or taskId not in self.tasks:
            return False
        if taskId in user['active'] or len(user['active']) >= user['quota']:
            return False
        self.seq += 1
        user['active'][taskId] = (finishTime, self.seq)
        heapq.heappush(user['heap'], (finishTime, self.seq, taskId))
        return True

    def getUserTasks(self, timestamp, userId):
        user = self._user(userId, timestamp)
        if user is None:
            return []
        return [taskId for _, _, taskId in sorted((f, s, taskId) for taskId, (f, s) in user['active'].items())]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TaskManager' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = TaskManager(*argument_lists[0])
    allowed = {'addTask', 'updateTask', 'getTask', 'searchTasks', 'listTasksSorted', 'addUser', 'assignTask', 'getUserTasks'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
