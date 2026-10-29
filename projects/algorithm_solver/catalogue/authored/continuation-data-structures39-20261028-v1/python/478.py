"""Original frontend 478 variant; qualification unknown."""


class Solution:
    def __init__(self, radius: float, x_center: float, y_center: float):
        self.radius = float(radius)
        self.xc = float(x_center)
        self.yc = float(y_center)
        self._state = 0x9E3779B9

    def _random(self) -> float:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state / 4294967296.0

    def randPoint(self):
        while True:
            dx = 2.0 * self._random() - 1.0
            dy = 2.0 * self._random() - 1.0
            if dx * dx + dy * dy <= 1.0:
                return [self.xc + self.radius * dx, self.yc + self.radius * dy]


def solve(operation_names, argument_lists):
    r, xc, yc = argument_lists[0]
    instance = Solution(r, xc, yc)
    out = [None]
    for op in operation_names[1:]:
        if op == "randPoint":
            out.append(instance.randPoint())
        else:
            raise ValueError("unknown operation")
    return out
