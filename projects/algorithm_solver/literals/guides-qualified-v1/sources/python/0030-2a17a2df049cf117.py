from collections import Counter
class Solution:

    def findSubstring(self, a, b):
        c = Counter(b)
        g, h = (len(a), len(b))
        d = len(b[0])
        e = []
        for f in range(d):
            i = j = f
            k = Counter()
            while j + d <= g:
                l = a[j:j + d]
                j += d
                if c[l] == 0:
                    i = j
                    k.clear()
                    continue
                k[l] += 1
                while k[l] > c[l]:
                    m = a[i:i + d]
                    i += d
                    k[m] -= 1
                if j - i == h * d:
                    e.append(i)
        return e
