import heapq
N, M = list(map(int, input().split()))
days = [[] for _ in range(M + 1)]
for i in range(N):
    a, b = list(map(int, input().split()))
    if a > M: continue
    days[a].append(b)

reward = []
heapq.heapify(reward)

total = 0
for i in range(M)[::-1]:
    tasks = days[M - i]
    for task in tasks:
        heapq.heappush(reward, -1 * task)

    if len(reward) > 0:
        total += heapq.heappop(reward) * (-1)

print(total)