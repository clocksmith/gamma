"""Original frontend 3926 variant; qualification unknown."""

def solve(chunks, queries):
    import re
    from collections import Counter
    counts = Counter(re.findall(r'[a-z]+(?:-[a-z]+)*', ''.join(chunks)))
    return [counts[word] for word in queries]


class Solution:
    def countWordOccurrences(self, chunks, queries):
        return solve(chunks, queries)
