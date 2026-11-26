H,W=map(int,input().split())
L=[]
for i in range(H):
    a=[]
    b=list(input())
    for j in range(W):
        if b[j]=="#":
            a.append(j)
    if a==[]:
        print("Impossible")
        exit()
    L.append([min(a),max(a)])
#print(L)
for i in range(1,H):
    if L[i][0]==L[i-1][1]:
        pass
    else:
        print("Impossible")
        exit()
print("Possible")