while True:
    N = int(input())
    if N == 0:
        break
    PPP = []

    for i in range(N):
        P = set(list(map(int, input().split()))[1:])
        PPP.append(P)


    K = set(list(map(int, input().split()))[1:])
    # print(PPP)
    # print(K)

    potential = []
    for i, p in enumerate(PPP):
        hoge = K - p
        if len(hoge) == 0:
            potential.append(i+1)

    if len(set(potential)) != 1:
        print(-1)
    else:
        print(potential[-1])

