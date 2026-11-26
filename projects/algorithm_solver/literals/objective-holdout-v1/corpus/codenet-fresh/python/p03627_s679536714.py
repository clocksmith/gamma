def spaceinput():
    return list(map(int,input().split(" ")))


N=int(input())
a=spaceinput()


sa=sorted(a,reverse=True)
x=[]
i=0
while True:
    if i>=len(sa)-1:
        break
    ssa=sa[i]
    if sa[i]==sa[i+1]:
        x.append(ssa)
        i+=2
        if len(x)==2:
            break
        continue

    else:
        i+=1


x.extend([0,0])

print(x[0]*x[1])