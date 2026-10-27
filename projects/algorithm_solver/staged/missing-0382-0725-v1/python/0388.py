"""388. Longest Absolute File Path. Maintain cumulative directory lengths by depth."""

def solve(input: str) -> int:
    lengths = [0]
    answer = 0
    for line in input.split('\n'):
        depth = len(line) - len(line.lstrip('\t'))
        name = line[depth:]
        while len(lengths) > depth + 1:
            lengths.pop()
        length = lengths[depth] + len(name)
        if '.' in name:
            answer = max(answer, length)
        else:
            lengths.append(length + 1)
    return answer


class Solution:
    def lengthLongestPath(self, input: str) -> int:
        return solve(input)
