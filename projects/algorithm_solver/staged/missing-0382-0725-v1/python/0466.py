"""466. Count The Repetitions. Skip repeated block-boundary automaton states."""

def solve(s1: str, n1: int, s2: str, n2: int) -> int:
    if n1 == 0 or not set(s2).issubset(set(s1)):
        return 0
    seen = {0: (0, 0)}
    block = index = matches = 0
    while block < n1:
        for char in s1:
            if char == s2[index]:
                index += 1
                if index == len(s2):
                    index = 0
                    matches += 1
        block += 1
        if index in seen:
            previous_block, previous_matches = seen[index]
            cycle_length = block - previous_block
            cycles = (n1 - block) // cycle_length
            if cycles:
                block += cycles * cycle_length
                matches += cycles * (matches - previous_matches)
        else:
            seen[index] = (block, matches)
    return matches // n2


class Solution:
    def getMaxRepetitions(self, s1: str, n1: int, s2: str, n2: int) -> int:
        return solve(s1, n1, s2, n2)
