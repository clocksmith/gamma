s=input()+"T"
x,y=map(int,input().split())
n=len(s)
prev=-1
cnt=0
x_,y_=[],[]
for i in range(n):
    if s[i]=="T":
        if cnt%2:
            y_.append(i-prev-1)
        else:
            x_.append(i-prev-1)
        cnt+=1
        prev=i
prevx=[0]*(2*n+1)
prevy=[0]*(2*n+1)
prevx[n+x_[0]]=1
prevy[n]=1
x_=x_[1:]
for num in x_:
    curx=[0]*(2*n+1)
    for i in range(2*n+1):
        if prevx[i]:
            if i-num>=0:
                curx[i-num]=1
            if i+num<=2*n:
                curx[i+num]=1
    prevx=curx
for num in y_:
    cury=[0]*(2*n+1)
    for i in range(2*n+1):
        if prevy[i]:
            if i-num>=0:
                cury[i-num]=1
            if i+num<=2*n:
                cury[i+num]=1
    prevy=cury
if prevy[y+n] and prevx[x+n]:
    print("Yes")
else:
    print("No")
#print(x_)
#print(y_)