n=int(input())
for i in range(n):
    count=0
    c,a,n=map(int,input().split())
    while n>0 and a>0 and c>0:
        n-=1
        a-=1
        c-=1
        count+=1
    while a>0 and c>1:
        a-=1
        c-=2
        count+=1
    while c>2:
        c-=3
        count+=1
    print(count)
