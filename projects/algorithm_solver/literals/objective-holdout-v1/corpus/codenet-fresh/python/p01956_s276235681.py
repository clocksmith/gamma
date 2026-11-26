n,h,w=map(int,input().split())
x=list(map(int,input().split()))
wide_total=n*w
wide_cover=[False]*wide_total

for i in range(n):
    if (i+1)%2==1:
        for j in range(i*w+x[i],i*w+x[i]+w):
            wide_cover[j]=True
    else:
        for j in range(i*w-x[i],i*w-x[i]+w):
            wide_cover[j]=True
cnt=0
for c in wide_cover:
    if c==False:
        cnt+=1

print(cnt*h)

