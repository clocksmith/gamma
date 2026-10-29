"""Hack2Hire 6ace8e7e2e3a0349b3a8e1d0 (Request Routing System, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

import re

INTEGER = re.compile(r'-?(0|[1-9][0-9]{0,8})')
LEVEL = 1


def parse(token, low, high):
    if INTEGER.fullmatch(token) is None:
        return None
    value = int(token)
    return value if low <= value <= high else None


class RequestRouter:
    def __init__(self):
        self.index = {}
        self.names, self.lat, self.lon, self.cap, self.up, self.load = [], [], [], [], [], []

    def processCommand(self, command):
        tokens = command.split(' ')
        head, size = tokens[0], len(tokens)
        if head == 'REGISTER' and size == 5:
            lat, lon, cap = parse(tokens[2], -90, 90), parse(tokens[3], -180, 180), parse(tokens[4], 1, 10**9)
            if lat is None or lon is None or cap is None or tokens[1] in self.index:
                return 'ERROR'
            self.index[tokens[1]] = len(self.names)
            for column, value in ((self.names, tokens[1]), (self.lat, lat), (self.lon, lon), (self.cap, cap), (self.up, True), (self.load, 0)):
                column.append(value)
            return 'OK'
        if head == 'ROUTE' and size == 3:
            lat, lon = parse(tokens[1], -90, 90), parse(tokens[2], -180, 180)
            if lat is None or lon is None:
                return 'ERROR'
            best = -1
            best_key = None
            for i in range(len(self.names)):
                if self.up[i] and self.load[i] < self.cap[i]:
                    dlat, dlon = self.lat[i] - lat, self.lon[i] - lon
                    key = (dlat * dlat + dlon * dlon, self.load[i], self.names[i])
                    if best_key is None or key < best_key:
                        best, best_key = i, key
            if best < 0:
                return 'ERROR'
            self.load[best] += 1
            return self.names[best]
        if LEVEL >= 2 and head in ('UP', 'DOWN') and size == 2:
            i = self.index.get(tokens[1])
            if i is None:
                return 'ERROR'
            self.up[i] = head == 'UP'
            return 'OK'
        if LEVEL >= 3 and head == 'RELEASE' and size == 2:
            i = self.index.get(tokens[1])
            if i is None or self.load[i] == 0:
                return 'ERROR'
            self.load[i] -= 1
            return 'OK'
        return 'ERROR'


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RequestRouter' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = RequestRouter(*argument_lists[0])
    allowed = ['processCommand']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in [] else value)
    return result
