import sys,queue,math,copy,itertools,bisect,collections,heapq

def main():
    sys.setrecursionlimit(10**7)
    INF = float('inf')
    MOD = 10**9 + 7
    LI = lambda : [int(x) for x in sys.stdin.readline().split()]
    _LI = lambda : [int(x)-1 for x in sys.stdin.readline().split()]
    NI = lambda : int(sys.stdin.readline())
    SI = lambda : sys.stdin.readline().rstrip()
    DD = ((1,0),(0,1),(-1,0),(0,-1))

    H,W,K = LI()
    x1,y1,x2,y2 = _LI()

    p = [SI() for _ in range(H)]

    d = [[INF] * W for _ in range(H)]
    d[x1][y1] = 0

    q = []
    q.append((0,x1,y1))
    while q:
        m,x,y =  heapq.heappop(q)
        if d[x][y] < m: continue
        d[x][y] = m
        for dx,dy in DD:
            for n in range(1,K+1):
                nx = x + dx * n
                ny = y + dy * n
                if not(0<=nx<H and 0<=ny<W): break
                if p[nx][ny] == '@': break
                if d[nx][ny] < m + 1: break
                if d[nx][ny] == m + 1: continue
                d[nx][ny] = m + 1
                q.append((m+1,nx,ny))
    if d[x2][y2] < INF:
        print(d[x2][y2])
    else:
        print(-1)



if __name__ == '__main__':
    main()