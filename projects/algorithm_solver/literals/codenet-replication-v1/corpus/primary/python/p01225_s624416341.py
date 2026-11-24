T=int(input())
for i in range(T):
    n=[int(i) for i in input().split()]
    c=[i for i in input().split()]
    R=[[],[],[]]
    for i in range(9):
        if c[i]=="R":
            R[0].append(n[i])
        elif c[i]=="G":        
            R[1].append(n[i])
        else:
            R[2].append(n[i])
    y=1
    i=0
 #   print(R)
    while y>0 and i<3:
        l=len(R[i])
        if l%3!=0:
            y=0
        else:
            R[i].sort()
            s=l//3
            j=0
            while y>0 and s>0 and j<len(R[i])-2:
                if R[i][j]==R[i][j+1]:
                    if R[i][j+1]==R[i][j+2]:
                        for k in range(3):
                            R[i].pop(j)
                        s-=1
                    elif R[i][j+1]+1==R[i][j+2]:
                        k=j+3
                        while k<len(R[i]) and R[i][k]==R[i][j+2]:
                            k+=1
                        if k>=len(R[i]) or R[i][k]!=R[i][j+2]+1:
                            y=0
                        else:
                            R[i].pop(k)
                            R[i].pop(j+2)
                            R[i].pop(j)
                        s-=1
                    else:
                        y=0
                elif R[i][j]+1==R[i][j+1]:
                    k=j+2
                    while k<len(R[i]) and R[i][k]==R[i][j+1]:
                        k+=1
                    if k>=len(R[i]) or R[i][k]!=R[i][j+1]+1:
                        y=0
                    else:
                        R[i].pop(k)
                        R[i].pop(j+1)
                        R[i].pop(j)
                        s-=1
                else:
                    y=0
        i+=1
    print(y)
