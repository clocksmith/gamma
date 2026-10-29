"""Hack2Hire 68c9ac13212d48d6e0f5977d (Thrilling Teleporters, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(teleporters, dieSides, lastSquare):
    target = list(range(lastSquare))
    for entry in teleporters:
        a, b = entry.split(',')
        target[int(a)] = int(b)
    dist = [-1] * (lastSquare + 1)
    dist[0] = 0
    queue = [0]
    head = 0
    while head < len(queue):
        square = queue[head]
        head += 1
        turns = dist[square] + 1
        if square + dieSides >= lastSquare:
            return turns
        for roll in range(1, dieSides + 1):
            nxt = target[square + roll]
            if nxt == lastSquare:
                return turns
            if dist[nxt] < 0:
                dist[nxt] = turns
                queue.append(nxt)
    return -1


class Solution:
    def minTurns(self, teleporters, dieSides, lastSquare):
        return solve(teleporters, dieSides, lastSquare)
