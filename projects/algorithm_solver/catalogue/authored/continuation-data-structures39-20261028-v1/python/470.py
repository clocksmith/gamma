"""Original frontend 470 variant; qualification unknown."""


def solve(rand7_stream=None) -> int:
    if rand7_stream is not None:
        for i in range(0, len(rand7_stream), 2):
            idx = (rand7_stream[i] - 1) * 7 + rand7_stream[i + 1]
            if idx <= 40:
                return (idx - 1) % 10 + 1
        return 1
    r7 = globals().get("rand7")
    while True:
        a = r7() if r7 is not None else 1
        b = r7() if r7 is not None else 1
        idx = (a - 1) * 7 + b
        if idx <= 40:
            return (idx - 1) % 10 + 1


rand10 = solve


class Solution:
    def rand10(self, rand7_stream=None) -> int:
        return solve(rand7_stream)
