"""Original hack2hire:6a6d1d1d48af2ae18e99352e; inferred public-preview contract; qualification unknown."""
def earliestReachableTime(startX, startY, targetX, targetY, directions):
    dx, dy = targetX - startX, targetY - startY
    if dx == dy == 0:
        return 0
    for time, direction in enumerate(directions, 1):
        if direction == 'E' and dx > 0:
            dx -= 1
        elif direction == 'W' and dx < 0:
            dx += 1
        elif direction == 'N' and dy > 0:
            dy -= 1
        elif direction == 'S' and dy < 0:
            dy += 1
        if dx == dy == 0:
            return time
    return -1

solve = earliestReachableTime

class Solution:
    earliestReachableTime = staticmethod(earliestReachableTime)
