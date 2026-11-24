import sys
def solve(n,m):
    d = [0]*n
    d_ = [0]*n
    for i in range(m):
        p = [int(x) for x in sys.stdin.readline().split()]
        for c in p[2:]:
            d[c-1] += p[0]
        if len(p) == 3:
            d_[p[2]-1] += p[0]
    ma = max(d)
    mi = min(d_)
    for i in range(n):
        if d[i] == ma:
            if d_[i] != mi:
                print(ma-mi+1)
                return
        else:
            if d_[i] == mi:
                print(ma-mi+1)
                return
    d.sort()
    d_.sort()
    print(max(d[-2]-mi,ma-d_[1])+1)
while 1:
    n,m = [int(x) for x in sys.stdin.readline().split()]
    if n == 0:
        break
    solve(n,m)

