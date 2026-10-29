"""Hack2Hire 68cdc7ec3735a578b6f27eec (Guess Number) over an INFERRED spec; qualification unknown."""

def solve(secret):
    log = []

    def guess_number(guess):
        log.append(guess)
        return sum(1 for a, b in zip(guess, secret) if a == b)

    count, known = [0] * 10, 0
    for digit in range(10):
        if known == 4:
            break
        if digit == 9:
            count[9] = 4 - known
            break
        answer = guess_number(str(digit) * 4)
        count[digit] = answer
        known += answer
        if answer == 4:
            return log
    filler = str(count.index(0))
    placed = ''
    for position in range(4):
        left = [d for d in range(10) if count[d] > 0]
        chosen = left[-1]
        if len(left) > 1:
            for d in left[:-1]:
                if guess_number(filler * position + str(d) + filler * (3 - position)) == 1:
                    chosen = d
                    break
        placed += str(chosen)
        count[chosen] -= 1
    if log[-1] != placed:
        guess_number(placed)
    return log


class Solution:
    def guessTranscript(self, secret):
        return solve(secret)
