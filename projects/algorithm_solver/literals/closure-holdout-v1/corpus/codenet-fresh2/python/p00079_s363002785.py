ans=0
x,y=map(float,input().split(","))
k1,k2=map(float,input().split(","))
while 1:
    try:
        k3,k4=map(float,input().split(","))
        a=((k1-x)**2+(k2-y)**2)**0.5
        b=((k3-x)**2+(k4-y)**2)**0.5
        c=((k1-k3)**2+(k2-k4)**2)**0.5
        z=(a+b+c)/2
        ans+=(z*(z-a)*(z-b)*(z-c))**0.5
        k1,k2=k3,k4
    except:break
print(ans)
