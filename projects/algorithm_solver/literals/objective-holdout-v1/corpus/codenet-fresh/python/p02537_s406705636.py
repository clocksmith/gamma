import sys
import heapq, math
from itertools import zip_longest, permutations, combinations, combinations_with_replacement
from itertools import accumulate, dropwhile, takewhile, groupby
from functools import lru_cache
from copy import deepcopy


def input():
    return sys.stdin.readline()[:-1]


class SegmentTree:

    def __init__(self, n, fn=lambda x, y: min(x, y), unity=(1 << 31) - 1):
        self.n = 1
        while self.n < n:
            self.n *= 2

        self.arr = [unity] * (2 * self.n - 1)
        self.fn = fn
        self.unity = unity

    def update(self, i, x):
        k = self.n + i
        self.arr[k] = x

        while k > 0:
            k >>= 1
            self.arr[k] = self.fn(self.arr[2 * k], self.arr[2 * k + 1])

    def query(self, l, r):
        l += self.n
        r += self.n
        lres, rres = self.unity, self.unity
        while l < r:
            # lが奇数ならば、dat[l]を加算
            if l & 1:
                lres = self.fn(lres, self.arr[l])
                l += 1

            # rが奇数ならば、dat[r-1]を加算
            if r & 1:
                r -= 1
                rres = self.fn(rres, self.arr[r])

            # 木をのぼる
            l >>= 1
            r >>= 1

        return self.fn(lres, rres)




    def __str__(self):
        return self.arr[0: 2 * self.n].__str__()


N, K = map(int, input().split())
MAX = 300000

st = SegmentTree(MAX + 10, fn=lambda x, y: max(x, y), unity=0)
ans = 0

while N > 0:
    A = int(input())
    minimum, maximum = max(A - K, 0), min(A + K, MAX)
    x = st.query(minimum, maximum + 1) + 1
    ans = max(ans, x)
    st.update(A, x)
    N -= 1

print(ans)
