#from itertools import groupby

def groupby(a):
    a2=[[a[0],1]]
    for i in range(1,len(a)):
        if a2[-1][0]==a[i]:
            a2[-1][1]+=1
        else:
            a2.append([a[i],1])
    return a2


s1=input()
k=int(input())

#s2=[[h, len(list(g))] for h, g in groupby(s1)]
s2=groupby(s1)

c=0
if len(s2)!=1:
    for i in range(len(s2)):
        if i!=0 and i!=len(s2)-1:
            c+=(s2[i][1]//2)*k

    if s2[0][0]==s2[-1][0]:
        c+=((s2[0][1]+s2[-1][1])//2)*(k-1)
        c+=(s2[0][1]//2+s2[-1][1]//2)
    else:
        c+=(s2[0][1]//2+s2[-1][1]//2)*k
else:
    c+=(s2[0][1]*k)//2

print(c)
