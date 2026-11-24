N=int(input())
for n in range(N):
    gx,gy=map(int,input().split())
    T=[[0 for i in range(gy+1)] for j in range(gx+1)]
    left=[[0 for i in range(gy+1)] for j in range(gx+1)]
    upper=[[0 for i in range(gy+1)] for j in range(gx+1)]
    p=int(input())
    for i in range(p):       
        x1,y1,x2,y2=map(int,input().split())
        if x1==x2:
            upper[x1][max(y1,y2)]=1
        if y1==y2:
            left[max(x1,x2)][y1]=1

    for i in range(gx+1):
        for j in range(gy+1):
            if i==0:
                left[i][j]=1
            if j==0:
                upper[i][j]=1
    for i in range(gx+1):
        for j in range(gy+1):
            if i==0 and j==0:
                T[i][j]=1
            else:  
                if left[i][j]==1 and upper[i][j]==1:
                    T[i][j]=0
                elif left[i][j]==0 and upper[i][j]==1:
                    T[i][j]=T[i-1][j]
                elif left[i][j]==1 and upper[i][j]==0:
                    T[i][j]=T[i][j-1]
                else:
                    T[i][j]=T[i-1][j]+T[i][j-1]

    if T[gx][gy]==0:
        print("Miserable Hokusai!")
    else:
        print(T[gx][gy])
