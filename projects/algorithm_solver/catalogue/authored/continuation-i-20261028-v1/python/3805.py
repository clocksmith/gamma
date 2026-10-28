def solve(words):
    counts = {}
    answer = 0
    for word in words:
        first = ord(word[0])
        key = tuple((ord(c) - first) % 26 for c in word)
        answer += counts.get(key, 0)
        counts[key] = counts.get(key, 0) + 1
    return answer


class Solution:
    def countPairs(self, words):
        return solve(words)
