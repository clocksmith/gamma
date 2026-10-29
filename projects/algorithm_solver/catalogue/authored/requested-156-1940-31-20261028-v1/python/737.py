"""Original frontend 737 variant; qualification unknown."""


def solve(sentence1, sentence2, similarPairs) -> bool:
    if len(sentence1) != len(sentence2):
        return False
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    for a, b in similarPairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return all(w1 == w2 or find(w1) == find(w2) for w1, w2 in zip(sentence1, sentence2))


areSentencesSimilarTwo = solve


class Solution:
    def areSentencesSimilarTwo(self, sentence1, sentence2, similarPairs) -> bool:
        return solve(sentence1, sentence2, similarPairs)
