n=int(input())
a,b=0,0
flag=0
for i in range(n):
    p,x=map(str,input().split())
    if p=="(":a+=int(x)
    else:b+=int(x)
    if a<b:
        flag=1
        break
if flag==1 or a!=b:print("NO")
else:print("YES")

