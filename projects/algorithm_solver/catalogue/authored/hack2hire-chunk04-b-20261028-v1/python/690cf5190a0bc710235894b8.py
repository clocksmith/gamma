"""Hack2Hire 690cf5190a0bc710235894b8 (Call Elevator) over an INFERRED spec; qualification unknown."""


def solve(elevators, request):
    floor = int(request[0])
    direction = request[1]
    best, best_distance = -1, -1
    for i, (f, state) in enumerate(elevators):
        f = int(f)
        if state == 'idle':
            eligible = True
        elif state != direction:
            eligible = False
        elif state == 'up':
            eligible = f <= floor
        else:
            eligible = f >= floor
        if eligible:
            distance = f - floor if f >= floor else floor - f
            if best < 0 or distance < best_distance:
                best, best_distance = i, distance
    return best


class Solution:
    def callElevator(self, elevators, request):
        return solve(elevators, request)
