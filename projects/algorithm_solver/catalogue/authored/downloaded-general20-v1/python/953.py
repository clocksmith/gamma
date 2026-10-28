"""953. Verifying an Alien Dictionary (Easy).

Specification: https://leetcode.com/problems/verifying-an-alien-dictionary/description/
"""


def solve(words: list[str], order: str) -> bool:
    rank = {ch: index for index, ch in enumerate(order)}
    for index in range(1, len(words)):
        previous = words[index - 1]
        current = words[index]
        compared = False
        for position in range(min(len(previous), len(current))):
            if previous[position] != current[position]:
                if rank[previous[position]] > rank[current[position]]:
                    return False
                compared = True
                break
        if not compared and len(previous) > len(current):
            return False
    return True


class Solution:
    def isAlienSorted(self, words: list[str], order: str) -> bool:
        return solve(words, order)
