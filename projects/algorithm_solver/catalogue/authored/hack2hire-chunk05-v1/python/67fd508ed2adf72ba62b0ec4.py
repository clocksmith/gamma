"""Original hack2hire:67fd508ed2adf72ba62b0ec4; inferred public-preview contract; qualification unknown."""
from collections import defaultdict

def shiftTimeline(schedules):
    order = list(dict.fromkeys(row[0] for row in schedules))
    events = defaultdict(lambda: defaultdict(int))
    for name, start, end in schedules:
        events[start][name] += 1
        events[end][name] -= 1
    times = sorted(events)
    counts = defaultdict(int)
    result = []
    for i, start in enumerate(times[:-1]):
        for name, delta in events[start].items():
            counts[name] += delta
        working = [name for name in order if counts[name] > 0]
        if not working:
            continue
        end = times[i + 1]
        if result and result[-1][1] == start and result[-1][2] == working:
            result[-1][1] = end
        else:
            result.append([start, end, working])
    return result

solve = shiftTimeline

class Solution:
    shiftTimeline = staticmethod(shiftTimeline)
