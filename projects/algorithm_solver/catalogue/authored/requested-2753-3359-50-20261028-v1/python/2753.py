"""Original frontend 2753 variant; qualification unknown."""


def solve(street, k: int) -> int:
    if isinstance(street, list):
        return len(street)
    while not street.isDoorOpen():
        street.moveRight()
    ans = 0
    for step in range(1, k + 1):
        street.moveRight()
        if street.isDoorOpen():
            ans = step
            street.closeDoor()
    return ans


houseCount = solve


class Solution:
    def houseCount(self, street, k: int) -> int:
        return solve(street, k)
