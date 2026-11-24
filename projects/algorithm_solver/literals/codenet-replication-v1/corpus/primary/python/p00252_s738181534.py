b1,b2,b3=map(int,input().split())
if b1==1 and b2==1 and  b3==0:
    print("Open")
elif b1==0 and b2==0 and b3==1:
    print("Open")
else:
    print("Close")
