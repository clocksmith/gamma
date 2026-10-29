"""Hack2Hire 6a121534653f4ff494e2c7ea (Camera Log Relay Server, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import deque


class CameraLogServer:
    def __init__(self):
        self._commands = {}  # cameraId -> deque of requested timestamps
        self._logs = deque()

    def requestLog(self, cameraId, timestamp):
        self._commands.setdefault(cameraId, deque()).append(timestamp)

    def pollCommand(self, cameraId):
        pending = self._commands.get(cameraId)
        return pending.popleft() if pending else -1

    def sendLog(self, cameraId, timestamp, log):
        self._logs.append((cameraId, timestamp, log))

    def pollLog(self):
        return list(self._logs.popleft()) if self._logs else None


def solve(operation_names, argument_lists):
    if operation_names[0] != 'CameraLogServer':
        raise ValueError('exact initial constructor required')
    instance = CameraLogServer(*argument_lists[0])
    allowed = ['requestLog', 'pollCommand', 'sendLog', 'pollLog']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
