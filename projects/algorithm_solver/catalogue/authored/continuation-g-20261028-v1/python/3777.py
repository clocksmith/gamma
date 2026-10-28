def solve(s, queries):
    text = list(s)
    n = len(text)
    tree = [0] * (n + 1)
    def add(i, delta):
        while i <= n:
            tree[i] += delta
            i += i & -i
    def prefix(i):
        total = 0
        while i:
            total += tree[i]
            i -= i & -i
        return total
    for i in range(1, n):
        if text[i - 1] == text[i]:
            add(i, 1)
    answer = []
    for q in queries:
        if q[0] == 1:
            j = q[1]
            affected = [i for i in (j, j + 1) if 1 <= i < n]
            before = [int(text[i - 1] == text[i]) for i in affected]
            text[j] = 'B' if text[j] == 'A' else 'A'
            for i, old in zip(affected, before):
                add(i, int(text[i - 1] == text[i]) - old)
        else:
            answer.append(prefix(q[2]) - prefix(q[1]))
    return answer


class Solution:
    def minDeletions(self, s, queries):
        return solve(s, queries)
