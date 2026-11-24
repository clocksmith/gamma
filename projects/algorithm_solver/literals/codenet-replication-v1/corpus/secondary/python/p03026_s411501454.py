N = int(input())

neighbors = [[] for _ in range(N)]

for _ in range(N - 1):
    a, b = map(int, input().split())
    a, b = a - 1, b - 1
    neighbors[a].append(b)
    neighbors[b].append(a)
c = list(map(int, input().split()))
sorted_c = sorted(c)

closed = [0 for _ in range(N)]
use = [0 for _ in range(N)]
q = []
q.append(0)
use[0] = sorted_c.pop()
M = 0


while len(q) > 0:
    parent = q.pop()
    closed[parent] = use[parent]
    for neighbor in neighbors[parent]:
        if closed[neighbor] == 0:
            c2 = use[neighbor] = sorted_c.pop()
            c1 = closed[parent]
            M += c2
            q.append(neighbor)

print(M)
print(*use)