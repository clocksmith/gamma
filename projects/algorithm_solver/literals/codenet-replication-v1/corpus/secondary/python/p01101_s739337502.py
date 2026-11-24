maxs=[]
while(True):
    max=-1
    
    b=list(map(int,input().split()))
    n=b[0]
    m=b[1]
    if(n == 0 and m == 0):
        break
    a=list(map(int,input().split()))
    for i in range(n):
        for j in range(i+1,n):
            sum=a[i]+a[j]
            if(sum>max and sum<=m):
                max=sum
    maxs.append(max)

for i in maxs:
    if i==-1:
        print("NONE")
    else:
        print(i)


