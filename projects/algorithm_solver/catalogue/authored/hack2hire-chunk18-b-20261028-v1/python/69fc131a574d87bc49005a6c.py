"""Hack2Hire 69fc131a574d87bc49005a6c (Data Labeling Task Scheduler, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def _parse(label, letter, top):
    if len(label) < 2 or label[0] != letter or label[1] == '0':
        return 0
    value = 0
    for ch in label[1:]:
        if ch < '0' or ch > '9':
            return 0
        value = value * 10 + ord(ch) - 48
    return value if value <= top else 0


def solve(totalTask, totalModel, totalHuman, k, schedule):
    counts = [0] * (totalTask + 1)
    humans = set()
    models = set()
    for triple in schedule:
        t = _parse(triple[0], 't', totalTask)
        m = _parse(triple[1], 'm', totalModel)
        h = _parse(triple[2], 'h', totalHuman)
        if not t or not m or not h:
            return False
        if (t, h) in humans or (t, m) in models:
            return False
        humans.add((t, h))
        models.add((t, m))
        counts[t] += 1
    for t in range(1, totalTask + 1):
        if counts[t] != k:
            return False
    return True


class Solution:
    def isValidSchedule(self, totalTask, totalModel, totalHuman, k, schedule):
        return solve(totalTask, totalModel, totalHuman, k, schedule)
