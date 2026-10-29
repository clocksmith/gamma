"""Original development candidate; independent qualification pending."""
from collections import deque

def solve(s1, s2):
    queue = deque([(s1,0)])
    seen = {s1}
    while queue:
        s,d = queue.popleft()
        if s == s2:
            return d
        i = next(i for i in range(len(s)) if s[i] != s2[i])
        for j in range(i+1,len(s)):
            if s[j] == s2[i] and s[j] != s2[j]:
                a = list(s)
                a[i],a[j] = a[j],a[i]
                t = ''.join(a)
                if t not in seen:
                    seen.add(t)
                    queue.append((t,d+1))


class Solution:
    def kSimilarity(self, s1, s2):
        return solve(s1, s2)
