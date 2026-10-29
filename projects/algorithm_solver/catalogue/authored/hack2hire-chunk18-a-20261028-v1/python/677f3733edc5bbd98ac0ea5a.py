"""Hack2Hire 677f3733edc5bbd98ac0ea5a (Highway Checkpoint) over an INFERRED spec; qualification unknown."""


def position(name):
    i = 0
    while not name[i].isdigit():
        i += 1
    return int(name[i:])


def solve(records):
    state = {}
    for plate, checkpoint in records:
        here = position(checkpoint)
        entry = state.get(plate)
        if entry is None:
            state[plate] = [here, 0]
        else:
            entry[1] += abs(here - entry[0]) * 10
            entry[0] = here
    return [[plate, state[plate][1]] for plate in sorted(state)]


class Solution:
    def calculateTolls(self, records):
        return solve(records)
