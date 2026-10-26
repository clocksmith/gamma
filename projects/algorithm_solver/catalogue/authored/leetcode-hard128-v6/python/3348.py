"""3348. Smallest Divisible Digit Product II.

Cover required prime exponents while choosing the rightmost feasible increment and lexicographically least suffix; O(9*L+log t) time and O(L) space. Inputs are preserved.
"""

def solve(num: str, t: int) -> str:
    factors = ((0, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0),
               (0, 1, 0, 0), (2, 0, 0, 0), (0, 0, 1, 0),
               (1, 1, 0, 0), (0, 0, 0, 1), (3, 0, 0, 0), (0, 2, 0, 0))
    required = [0] * 4
    for index, prime in enumerate((2, 3, 5, 7)):
        while t % prime == 0:
            required[index] += 1
            t //= prime
    if t != 1:
        return '-1'

    def consume(state, digit):
        return tuple(max(0, state[index] - factors[digit][index]) for index in range(4))

    def needed(state):
        twos, threes, fives, sevens = state
        answer = fives + sevens + twos // 3 + threes // 2
        twos, threes = twos % 3, threes % 2
        return answer + (twos + 1) // 2 + threes - int(twos == 1 and threes == 1)

    def fill(state, length):
        result = []
        for remaining in range(length - 1, -1, -1):
            for digit in range(1, 10):
                following = consume(state, digit)
                if needed(following) <= remaining:
                    result.append(str(digit))
                    state = following
                    break
        return ''.join(result)

    prefixes = [tuple(required)]
    first_zero = len(num)
    for index, character in enumerate(num):
        if character == '0':
            first_zero = index
            break
        prefixes.append(consume(prefixes[-1], int(character)))
    if first_zero == len(num) and needed(prefixes[-1]) == 0:
        return num
    for index in range(min(first_zero, len(num) - 1), -1, -1):
        remaining = len(num) - index - 1
        for digit in range(int(num[index]) + 1, 10):
            state = consume(prefixes[index], digit)
            if needed(state) <= remaining:
                return num[:index] + str(digit) + fill(state, remaining)
    length = max(len(num) + 1, needed(required))
    return fill(tuple(required), length)


class Solution:
    def smallestNumber(self, num: str, t: int) -> str:
        return solve(num, t)
