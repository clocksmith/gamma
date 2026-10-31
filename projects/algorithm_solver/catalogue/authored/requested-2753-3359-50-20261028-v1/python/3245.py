"""Original frontend 3245 variant; qualification unknown."""

import bisect


def solve(colors, queries):
    arr = list(colors)
    n = len(arr)
    bit_cnt = [0] * (n + 2)
    bit_sum = [0] * (n + 2)

    def bit_add(length: int, delta: int):
        idx = length
        val = length * delta
        while idx <= n + 1:
            bit_cnt[idx] += delta
            bit_sum[idx] += val
            idx += idx & -idx

    def bit_query(idx: int):
        c = 0
        s = 0
        while idx > 0:
            c += bit_cnt[idx]
            s += bit_sum[idx]
            idx -= idx & -idx
        return c, s

    cuts = []
    for i in range(n):
        if arr[i] == arr[(i + 1) % n]:
            cuts.append(i)
    m = len(cuts)
    for j in range(m):
        prev = cuts[j - 1]
        cur = cuts[j]
        dist = (cur - prev) % n
        if dist == 0:
            dist = n
        bit_add(dist, 1)

    def insert_cut(pos: int):
        idx = bisect.bisect_left(cuts, pos)
        if idx < len(cuts) and cuts[idx] == pos:
            return
        if not cuts:
            cuts.append(pos)
            bit_add(n, 1)
            return
        prev = cuts[idx - 1] if idx > 0 else cuts[-1]
        nxt = cuts[idx] if idx < len(cuts) else cuts[0]
        old_d = (nxt - prev) % n
        if old_d == 0:
            old_d = n
        bit_add(old_d, -1)
        d1 = (pos - prev) % n
        d2 = (nxt - pos) % n
        bit_add(d1, 1)
        bit_add(d2, 1)
        cuts.insert(idx, pos)

    def remove_cut(pos: int):
        idx = bisect.bisect_left(cuts, pos)
        if idx == len(cuts) or cuts[idx] != pos:
            return
        if len(cuts) == 1:
            cuts.pop()
            bit_add(n, -1)
            return
        prev = cuts[idx - 1] if idx > 0 else cuts[-1]
        nxt = cuts[idx + 1] if idx + 1 < len(cuts) else cuts[0]
        d1 = (pos - prev) % n
        d2 = (nxt - pos) % n
        bit_add(d1, -1)
        bit_add(d2, -1)
        new_d = (nxt - prev) % n
        if new_d == 0:
            new_d = n
        bit_add(new_d, 1)
        cuts.pop(idx)

    out = []
    for q in queries:
        if q[0] == 1:
            sz = q[1]
            if not cuts:
                out.append(n)
            else:
                tot_c, tot_s = bit_query(n)
                lo_c, lo_s = bit_query(sz - 1)
                c = tot_c - lo_c
                s = tot_s - lo_s
                out.append(s - (sz - 1) * c)
        else:
            idx, col = q[1], q[2]
            if arr[idx] == col:
                continue
            arr[idx] = col
            for p in ((idx - 1) % n, idx):
                if arr[p] == arr[(p + 1) % n]:
                    insert_cut(p)
                else:
                    remove_cut(p)
    return out


numberOfAlternatingGroups = solve


class Solution:
    def numberOfAlternatingGroups(self, colors, queries):
        return solve(colors, queries)
