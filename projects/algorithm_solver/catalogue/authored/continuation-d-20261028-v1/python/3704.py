"""Original development candidate for frontend 3704; qualification pending."""

def solve(n):
    states = {(0, False, False): 1}
    for position, target in enumerate(map(int, reversed(str(n)))):
        following = {}
        for (carry, ended_a, ended_b), count in states.items():
            for a in ([0] if ended_a else range(1 if position == 0 else 0, 10)):
                for b in ([0] if ended_b else range(1 if position == 0 else 0, 10)):
                    value = a + b + carry
                    if value % 10 == target:
                        key = (value // 10, ended_a or a == 0, ended_b or b == 0)
                        following[key] = following.get(key, 0) + count
        states = following
    return sum(count for (carry, _, _), count in states.items() if carry == 0)


class Solution:
    def countNoZeroPairs(self, n):
        return solve(n)
