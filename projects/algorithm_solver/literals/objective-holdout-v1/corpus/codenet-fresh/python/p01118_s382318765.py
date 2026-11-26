while True:
    h,w = map(int,input().split())
    if(h+w == 0):
        break
    li = list()
    for i in range(h):
        s = input()
        li.append(s)
    d = dict()
    for i,l in enumerate(li):
        for j,char in enumerate(l):
            d[char] = (i,j)
    target = input()
    ans = 0
    now = (0,0)
    for t in target:
        next = d[t]
        ans += abs(now[0]-next[0]) + abs(now[1]-next[1])
        now=next
    print(ans + len(target))
