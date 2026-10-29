"""Original Hack2Hire 6a4e6cd2665efda9311f4d82 variant over an INFERRED specification (injected automaton); qualification unknown."""


def solve(input, transitions, start, accepting):
    state = start
    for ch in input:
        state = transitions[state][0 if ch == 'a' else 1]
    return state in set(accepting)


class Solution:
    def simulateDfa(self, input, transitions, start, accepting):
        return solve(input, transitions, start, accepting)
