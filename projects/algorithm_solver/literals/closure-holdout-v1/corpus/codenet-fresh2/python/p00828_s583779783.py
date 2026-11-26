import sys
sys.setrecursionlimit(1000000000)
input=lambda : sys.stdin.readline().rstrip()

dx=[1,1,0,-1,1,1,0,-1,-1,-1,0,1,0]
dy=[0,1,1,1,0,1,1,1,0,-1,-1,-1,0]
dz=[0,0,0,0,1,1,1,1,1,1,1,1,1]

while True:
    n,m,q=map(int,input().split())
    if n==m==q==0:
        break
    field=[[[-1 for i in range(n)]for i in range(n)]for i in range(n)]
    d=True
    turn=1
    for t in range(q):
        x,y=map(int,input().split())
        if d==False:
            continue
        x,y=x-1,y-1
        z=n
        while z>0:
            if field[x][y][z-1]==-1:
                z-=1
            else:
                break
        field[x][y][z]=turn
        for i in range(13):
            tx,ty,tz=x,y,z
            count=0
            while 0<=tx<n and 0<=ty<n and 0<=tz<n:
                if field[tx][ty][tz]==turn:
                    count+=1
                else:
                    break
                tx,ty,tz=tx+dx[i],ty+dy[i],tz+dz[i]
            tx,ty,tz=x,y,z
            while 0<=tx<n and 0<=ty<n and 0<=tz<n:
                if field[tx][ty][tz]==turn:
                    count+=1
                else:
                    break
                tx,ty,tz=tx-dx[i],ty-dy[i],tz-dz[i]
            count-=1
            if count>=m:
                print('Black' if turn else 'White',t+1)
                d=False
                break
        turn=(turn+1)%2
    if d:
        print('Draw')


