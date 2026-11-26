while True:
    t, p, r = map(int, input().split())
    if t == p == r == 0:
        break

    data = [[0 for i in range(p + 1)] for i in range(t + 1)]
    for i in range(r):
        li = input().split()
        tid, pid, time = map(int, li[:3])
        if li[3] == "WRONG":
            data[tid][pid] -= 1
        else:
            data[tid][pid] = time - data[tid][pid] * 1200

    rank = list()
    for tid in range(1, t + 1):
        ans, pen = 0, 0
        for pid in range(1, p + 1):
            if data[tid][pid] > 0:
                ans -= 1
                pen += data[tid][pid]
        rank.append((ans, pen, tid))

    for ans, pen, tid in sorted(rank):
        print(tid, -ans, pen)
