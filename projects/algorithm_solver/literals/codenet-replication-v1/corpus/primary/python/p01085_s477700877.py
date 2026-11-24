while True:
    sa_max = 0
    Sa = []
    num = 0
    Poi_lis = []
    m,nmin,nmax = map(int,input().split())
    if [m,nmin,nmax] == [0,0,0]:
        break
    for i in range(m):
        Poi_lis.append(int(input()))
        if nmin + 1 <= i + 1 <= nmax + 1:
            Sa.append(Poi_lis[i - 1] - Poi_lis[i])
    Sa_r = Sa[::-1]
    
    cou = Sa_r.index(max(Sa_r))
    print(nmin + len(Sa) - cou - 1)