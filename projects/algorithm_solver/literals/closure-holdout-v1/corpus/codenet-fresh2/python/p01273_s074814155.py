while True:
    N,M = map(int,input().split())
    if N == M == 0: break
    logs = []
    for i in range(M):
        t,s,d = map(int,input().split())
        s,d = s-1,d-1
        logs.append((t,s,d))
    infected = [0 for i in range(N)]
    infected[0] = 1
    for t,s,d in sorted(logs):
        if infected[s]:
            infected[d] = 1
    print(sum(infected))