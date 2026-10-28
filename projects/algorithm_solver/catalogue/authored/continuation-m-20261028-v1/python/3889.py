from collections import Counter


def solve(s):
    counts = Counter(s)
    answer = 0
    for alphabet in ('abcdefghijklmnopqrstuvwxyz', '0123456789'):
        for i in range(len(alphabet) // 2):
            answer += abs(counts[alphabet[i]] - counts[alphabet[-i - 1]])
    return answer


class Solution:
    def mirrorFrequency(self, s):
        return solve(s)
