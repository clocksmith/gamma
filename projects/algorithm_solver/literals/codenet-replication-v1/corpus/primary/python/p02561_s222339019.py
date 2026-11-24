class maxflow():
    def __init__(self, n):
        self.pos = []
        self.g = [[] for _ in range(n)]
        self.n = n
    
    def add_edge(self, v, w, cap):
        e1 = [w, 0, cap]
        e2 = [v, e1, 0]
        e1[1] = e2
        self.g[v].append(e1)
        self.g[w].append(e2)
    
    def flow(self, s, t, flow_limit = -1):
        if flow_limit < 0: flow_limit = 10 ** 100
        def bfs():
            L = [-1] * self.n
            L[s] = 0
            Q = [s]
            while Q:
                v = Q.pop()
                for w, _, cap in self.g[v]:
                    if cap == 0 or L[w] >= 0: continue
                    L[w] = L[v] + 1
                    if w == t: return L
                    Q.append(w)
            return L
        
        def dfs(v, up):
            if v == s: return up
            res = 0
            lv = L[v]
            for i in range(it[v], len(self.g[v])):
                w, rev, cap = self.g[v][i]
                if lv <= L[w] or rev[2] == 0: continue
                
                d = dfs(w, min(up - res, rev[2]))
                if d <= 0: continue
                self.g[v][i][2] += d
                rev[2] -= d
                res += d
                if res == up: break
                it[v] += 1
            return res
        
        flow = 0
        while flow < flow_limit:
            L = bfs()
            if L[t] == -1: break
            it = [0] * self.n
            while flow < flow_limit:
                f = dfs(t, flow_limit - flow)
                if not f: break
                flow += f
        return flow, self.g
    
    def min_cut(self, s):
        visited = [0] * self.n
        Q = [s]
        while Q:
            p = Q.pop()
            visited[p] = 1
            for e in self.g[p]:
                if e[2] and visited[e[0]] == 0:
                    visited[e[0]] = 1
                    Q.append(e[0])
        return visited

N, M = map(int, input().split())
mf = maxflow(N * M + 2)
A = [[a for a in input()] for _ in range(N)]
X = [[1 if a == "." else 0 for a in aa] for aa in A]
s = N * M
t = s + 1
for i in range(N):
    for j in range(M):
        if X[i][j]:
            if (i ^ j) & 1 == 0:
                mf.add_edge(s, i * M + j, 1)
            else:
                mf.add_edge(i * M + j, t, 1)

for i in range(N - 1):
    for j in range(M):
        if X[i][j] and X[i+1][j]:
            a = i * M + j
            b = a + M
            if (i ^ j) & 1 == 0:
                mf.add_edge(a, b, 1)
            else:
                mf.add_edge(b, a, 1)
for i in range(N):
    for j in range(M - 1):
        if X[i][j] and X[i][j+1]:
            a = i * M + j
            b = a + 1
            if (i ^ j) & 1 == 0:
                mf.add_edge(a, b, 1)
            else:
                mf.add_edge(b, a, 1)

fl, g = mf.flow(s, t)
# print("fl =", fl, g)
for v, gv in enumerate(g):
    if v >= N * M: continue
    for w, _, ca in gv:
        if w >= N * M: continue
        # if w > v: v, w = w, v
        vi, vj = v // M, v % M
        wi, wj = w // M, w % M
        if (vi ^ vj) % 2 == 0 and ca == 0:
            if v > w:
                vi, vj, wi, wj = wi, wj, vi, vj
            # print("v, w, ca =", v, w, ca)
            if vi == wi:
                A[vi][vj] = ">"
                A[wi][wj] = "<"
            else:
                A[vi][vj] = "v"
                A[wi][wj] = "^"

print(fl)
for x in A:
    print("".join(map(str, x)))
