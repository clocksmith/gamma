n,k=map(int,input().split())
statas=input()
subs=[]
count=1
buf=statas[0]
for string in statas[1:]:
    if buf==string:
        count+=1
    else:
        subs.append(count)
        count=1
        buf=string
if (len(subs)+1)//2 <= k:
    print(n-1)
else:
    print(n-1-len(subs)+2*k)