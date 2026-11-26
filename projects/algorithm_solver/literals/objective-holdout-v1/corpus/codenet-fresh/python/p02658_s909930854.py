n=int(input())
a=input().split()
a=list(map(int,a))
ans=1
if(0 in a):
    print(0)
    exit()

for calc in a:
    ans*=calc
    if(ans>10**18):
        print(-1)
        exit()
if(ans>10**18):
    print(-1)
else:
    print(ans)
