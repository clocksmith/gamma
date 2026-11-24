s=input()
l=len(s)
ans=101
if len(set(s))==1:
    print(0)
    exit()
for target in s:
    a=s
    for i in range(l):
        tmp=[]
        for j in range(l-i-1):
            if a[j]==target or a[j+1]==target:
                tmp.append(target)
            else:
                tmp.append(a[j])
        a=tmp
        if len(set(a))==1:
            ans=min(ans,i+1)
            break
print(ans)