"""3441. Minimum Cost Good Caption.

Suffix dynamic programming tracks the last letter and run length capped at three, then greedily reconstructs the smallest optimum; O(26*n) time and space. Input is preserved.
"""

from array import array


def solve(caption: str) -> str:
    n = len(caption)
    if n < 3:
        return ''
    infinity, width = 1_000_000_000, 78
    cost = array('i', [infinity]) * ((n + 1) * width)
    for letter in range(26):
        cost[n * width + 3 * letter + 2] = 0
    for index in range(n - 1, -1, -1):
        original = ord(caption[index]) - 97
        following, current = (index + 1) * width, index * width
        first = second = infinity
        first_letter = -1
        for letter in range(26):
            value = abs(original - letter) + cost[following + 3 * letter]
            if value < first:
                first, second, first_letter = value, first, letter
            elif value < second:
                second = value
        for letter in range(26):
            difference, offset = abs(original - letter), 3 * letter
            cost[current + offset] = difference + cost[following + offset + 1]
            cost[current + offset + 1] = difference + cost[following + offset + 2]
            cost[current + offset + 2] = min(difference + cost[following + offset + 2], first if first_letter != letter else second)
    remaining = min(abs(ord(caption[0]) - 97 - letter) + cost[width + 3 * letter] for letter in range(26))
    answer = []
    previous, run = -1, 0
    for index, character in enumerate(caption):
        original = ord(character) - 97
        for letter in range(26):
            if previous != -1 and previous != letter and run < 3:
                continue
            length = min(3, run + 1) if previous == letter else 1
            difference = abs(original - letter)
            if difference + cost[(index + 1) * width + 3 * letter + length - 1] == remaining:
                answer.append(chr(97 + letter))
                remaining -= difference
                previous, run = letter, length
                break
    return ''.join(answer)


class Solution:
    def minCostGoodCaption(self, caption: str) -> str:
        return solve(caption)
