"""Hack2Hire 69ab8d9d4b133b6a8f3a699f (Thread Logs Processing, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(logs):
    keys = []
    for index, entry in enumerate(logs):
        process, thread, stamp, _ = entry.split(':', 3)
        keys.append((process, thread, int(stamp), index))
    keys.sort()
    return [logs[key[3]] for key in keys]


class Solution:
    def sortLogs(self, logs):
        return solve(logs)
