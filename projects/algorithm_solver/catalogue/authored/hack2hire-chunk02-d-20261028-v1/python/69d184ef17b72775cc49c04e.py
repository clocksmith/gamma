"""Hack2Hire 69d184ef17b72775cc49c04e (File System Permissions) over an INFERRED spec; qualification unknown."""
from bisect import bisect_right


def solve(teams, queries):
    enter, leave = {}, {}
    grants = {}
    clock = 0
    stack = [(node, False) for node in reversed(teams)]
    while stack:
        node, done = stack.pop()
        uuid = node['uuid']
        if done:
            leave[uuid] = clock - 1
            continue
        enter[uuid] = clock
        clock += 1
        for user in node['userIds']:
            grants.setdefault(user, []).append(uuid)
        stack.append((node, True))
        for child in reversed(node['children']):
            stack.append((child, False))
    outer = {}
    for user, uuids in grants.items():
        starts, ends = [], []
        for uuid in sorted(uuids, key=enter.get):
            if ends and enter[uuid] <= ends[-1]:
                continue
            starts.append(enter[uuid])
            ends.append(leave[uuid])
        outer[user] = (starts, ends)
    result = []
    for user, uuid in queries:
        spans = outer.get(user)
        if spans is None or uuid not in enter:
            result.append(False)
            continue
        position = enter[uuid]
        i = bisect_right(spans[0], position) - 1
        result.append(i >= 0 and spans[1][i] >= position)
    return result


class Solution:
    def checkAccess(self, teams, queries):
        return solve(teams, queries)
