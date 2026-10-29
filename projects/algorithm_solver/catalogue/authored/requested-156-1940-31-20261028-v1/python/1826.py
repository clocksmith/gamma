"""Original frontend 1826 variant; qualification unknown."""


def solve(sensor1, sensor2) -> int:
    n = len(sensor1)
    i = 0
    while i < n and sensor1[i] == sensor2[i]:
        i += 1
    if i >= n - 1:
        return -1
    ok1 = sensor1[i : n - 1] == sensor2[i + 1 : n]
    ok2 = sensor2[i : n - 1] == sensor1[i + 1 : n]
    if ok1 and not ok2:
        return 1
    if ok2 and not ok1:
        return 2
    return -1


badSensor = solve


class Solution:
    def badSensor(self, sensor1, sensor2) -> int:
        return solve(sensor1, sensor2)
