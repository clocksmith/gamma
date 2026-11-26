n=int(input())
for i in range(n):
    x,y,b,p=map(int,input().split())
    if b>=5 and p>=2:
        print(int((x*b+y*p)*0.8))
    else:
        keep=x*b+y*p
        if b<5:b=5
        if p<2:p=2
        keep2=int((x*b+y*p)*0.8)
        print(min(keep,keep2))
