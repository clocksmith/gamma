n=int(input())
a,b=map(int,input().split())
c=int(input())
A=a
C=c
top=[]
for i in range(n):
    top.append(int(input()))
top.sort(reverse=True)
ans=C/A
for i in top:
    C+=i
    A+=b
    now=C/A
    if ans<now:ans=now
    elif ans>=now:break
print(int(ans))
