"""Original frontend 911 variant; qualification unknown."""

import bisect
from collections import defaultdict


class TopVotedCandidate:
    def __init__(self, persons, times):
        self.times = list(times)
        counts = defaultdict(int)
        self.leaders = []
        cur_leader = -1
        max_votes = 0
        for p in persons:
            counts[p] += 1
            if counts[p] >= max_votes:
                max_votes = counts[p]
                cur_leader = p
            self.leaders.append(cur_leader)

    def q(self, t: int) -> int:
        idx = bisect.bisect_right(self.times, t) - 1
        return self.leaders[idx]


def solve(operation_names, argument_lists):
    inst = TopVotedCandidate(*argument_lists[0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        out.append(inst.q(args[0]))
    return out
