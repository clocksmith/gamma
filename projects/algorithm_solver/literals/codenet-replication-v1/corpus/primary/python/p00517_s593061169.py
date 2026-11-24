w,h,n=map(int,input().split())
x,y=map(int,input().split())
ans=0
for i in range(n-1):
    xi,yi=map(int,input().split())
    if xi==x:
        ans+=abs(y-yi)
        y=yi
    elif yi==y:
        ans+=abs(x-xi)
        x=xi
    elif (x-xi)*(y-yi)>0:
        ans+=max(abs(x-xi),abs(y-yi))
        x,y=xi,yi
    else:
        ans+=abs(x-xi)+abs(y-yi)
        x,y=xi,yi
print(ans)
