"""Hack2Hire 695572104a0202df9569e960 (Merge JSON Event Logs) over an INFERRED spec; qualification unknown."""

import heapq


def solve(logs):
    heap = []
    for server, events in logs.items():
        if events:
            heap.append((events[0]['time'], server, 0))
    heapq.heapify(heap)
    out = []
    while heap:
        time, server, position = heapq.heappop(heap)
        events = logs[server]
        event = events[position]
        merged = {'serverId': server, 'time': event['time'], 'type': event['type']}
        if 'target' in event:
            merged['target'] = event['target']
        out.append(merged)
        if position + 1 < len(events):
            heapq.heappush(heap, (events[position + 1]['time'], server, position + 1))
    return out


class Solution:
    def mergeEventLogs(self, logs):
        return solve(logs)
