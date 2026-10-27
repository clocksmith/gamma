from math import isqrt


def solve(s):
    candidates = {int(s[left:right]) for left in range(len(s))
                  for right in range(left + 1, len(s) + 1)}
    answer = count = 0
    for number in sorted(candidates, reverse=True):
        if number < 2 or (number != 2 and number % 2 == 0):
            continue
        if all(number % divisor for divisor in range(3, isqrt(number) + 1, 2)):
            answer += number
            count += 1
            if count == 3:
                break
    return answer
