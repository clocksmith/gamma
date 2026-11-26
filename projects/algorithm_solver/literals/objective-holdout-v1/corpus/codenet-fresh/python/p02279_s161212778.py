class node:
    def __init__(self, parent, left, right, depth):
        self.p = parent
        self.l = left
        self.r = right
        self.d = depth

def getDepth(u):
    depth = 0
    c = u
    while T[c].p != -1:
        depth += 1
        c = T[c].p
    T[u].d = depth

def getChildren(u):
    c = T[u].l
    children = []
    while c != -1:
        children.append(c)
        c = T[c].r
    return children

n = int(input())
T = [node(-1, -1, -1, 0) for _ in range(n)]
for i in range(n):
    info = list(map(int, input().split(" ")))
    for j in range(info[1]):
        if j == 0:
            T[info[0]].l = info[2 + j]
        else:
            T[info[2 + j - 1]].r = info[2 + j]
        T[info[2 + j]].p = info[0]

for i in range(n):
    print("node", end = ' ')
    print(i, end = ': ')
    print("parent =", end = ' ')
    print(T[i].p, end = ', ')
    print("depth =", end = ' ')
    getDepth(i)
    print(T[i].d, end = ', ')
    if T[i].p == -1: print("root", end = ', ')
    elif T[i].l == -1: print("leaf", end = ', ')
    else: print("internal node", end = ', ')
    print(getChildren(i))

