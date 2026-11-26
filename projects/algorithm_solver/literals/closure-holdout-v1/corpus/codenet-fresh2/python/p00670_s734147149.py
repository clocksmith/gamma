while 1:
    n,s=map(int,input().split())
    if n==0:break
    r=[0]*101
    for _ in [0]*n:r[int(input())]+=1
    a=0
    for i in range(101):
        if i*2>s:a+=(r[i]**2-r[i])//2
        a+=r[i]*sum(r[j] for j in range(max(i+1,s+1-i),101))
    print(a)