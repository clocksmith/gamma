#C
inf = float("inf")
N,M = map(int,input().split())
flag = [list(str(input())) for i in range(N)]
WBR = []

for i in range(N):
    w = flag[i].count("W")
    b = flag[i].count("B")
    r = flag[i].count("R")
    WBR.append([w,b,r])
    
    
ans = inf
for w in range(N-2):
    for b in range(N-1):
        if w >= b:
            pass
        else:
            kari = 0
            for i in range(N):
                if i <= w:
                    kari+=(M-WBR[i][0])
                elif i <= b:
                    kari+=(M-WBR[i][1])
                else:
                    kari+=(M-WBR[i][2])
            ans = min(ans,kari)
                    
print(ans)



