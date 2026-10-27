"""527. Word Abbreviation. Neighbor longest-common-prefix lengths resolve collisions within equal length/first/last groups."""

from collections import defaultdict

def solve(words: list[str]) -> list[str]:
    groups = defaultdict(list)
    for i, word in enumerate(words):
        groups[(len(word), word[0], word[-1])].append(i)
    answer = words[:]
    def common(a, b):
        length = 0
        while length < min(len(a), len(b)) and a[length] == b[length]:
            length += 1
        return length
    for indices in groups.values():
        indices.sort(key=lambda i: words[i])
        for position, index in enumerate(indices):
            word = words[index]
            shared = 0
            if position:
                shared = max(shared, common(word, words[indices[position - 1]]))
            if position + 1 < len(indices):
                shared = max(shared, common(word, words[indices[position + 1]]))
            prefix = max(1, shared + 1)
            skipped = len(word) - prefix - 1
            if skipped > 0:
                abbreviation = word[:prefix] + str(skipped) + word[-1]
                if len(abbreviation) < len(word):
                    answer[index] = abbreviation
    return answer


class Solution:
    def wordsAbbreviation(self, words: list[str]) -> list[str]:
        return solve(words)
