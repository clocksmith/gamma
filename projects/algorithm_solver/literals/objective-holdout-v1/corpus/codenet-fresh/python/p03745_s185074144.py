n=int(input())
pre=0
ans=1
t=0
for i in input().split():
    a=int(i)
    if pre==0:
        pre=a
    else:
        if pre>a:
            if -t<0 and t**2==1:
                ans+=1
                t=-2
            else:
                t=-1
        elif pre<a:
            if t<0 and t**2==1:
                ans+=1
                t=2
            else:
                t=1
        else:
            continue
        pre=a
print(ans)