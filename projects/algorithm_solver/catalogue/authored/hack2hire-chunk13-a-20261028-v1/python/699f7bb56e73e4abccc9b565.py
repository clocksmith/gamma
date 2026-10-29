"""Hack2Hire 699f7bb56e73e4abccc9b565 (Rank Vehicles by Contribution) over an INFERRED spec; qualification unknown."""


def solve(events):
    sent = {}
    for source, chunk_list, target in events:
        if source != 'server':
            sent[source] = sent.get(source, 0) + chunk_list.count(' ') + 1
        if target not in sent:
            sent[target] = 0
    return sorted(sent, key=lambda v: (-sent[v], v))


class Solution:
    def rankVehicles(self, events):
        return solve(events)
