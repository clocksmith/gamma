s = int(input())
ss = list()
ss += [s]
ans = 1
for i in range(1000000000):    
    if s%2 == 0:
        s = s//2
    else:
        s = 3*s+1
    ss += [s]
    ans +=1
    if s in ss[:-1]:
        print(ans)
        break
    