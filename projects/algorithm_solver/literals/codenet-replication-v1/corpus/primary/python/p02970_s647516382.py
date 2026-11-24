n,d=map(int,input().split())
x=2*d+1
if(n%x!=0):
    print(int(n/x)+1)
else:
    print(int(n/x))


