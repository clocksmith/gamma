while True:
    n,m=map(int,input().split())
    if n==0 and m==0:
        break
    a=[int(x) for x in input().split()]
    ans=0
    for i in a:
        if i<m//n:
            ans+=i
        else:
            ans+=m//n
    print(ans)
