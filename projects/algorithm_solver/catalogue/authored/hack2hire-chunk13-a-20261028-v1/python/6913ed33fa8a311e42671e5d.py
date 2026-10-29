"""Hack2Hire 6913ed33fa8a311e42671e5d (Pin Board Connectivity, variant 2) over an INFERRED spec; qualification unknown."""


def solve(boards, pin1, pin2):
    on = {}  # pin -> indices of the boards holding it
    for b, board in enumerate(boards):
        for pin in board:
            on.setdefault(pin, []).append(b)
    if pin1 not in on or pin2 not in on:
        return -1
    dist = [0] * len(boards)  # 0 = not reached
    queue = []
    for b in on[pin1]:
        dist[b] = 1
        queue.append(b)
    expanded = {pin1}
    head = 0
    while head < len(queue):
        b = queue[head]
        head += 1
        for pin in boards[b]:
            if pin == pin2:
                return dist[b]
            if pin in expanded:
                continue
            expanded.add(pin)
            for nb in on[pin]:
                if dist[nb] == 0:
                    dist[nb] = dist[b] + 1
                    queue.append(nb)
    return -1


class Solution:
    def minBoardsBetweenPins(self, boards, pin1, pin2):
        return solve(boards, pin1, pin2)
