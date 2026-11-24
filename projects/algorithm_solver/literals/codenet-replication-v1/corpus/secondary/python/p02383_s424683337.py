label = list(map(int,input().split()))
direction = list(str(input()))
D=list(range(6))
Dtemp=[0,0,0,0,0,0]
for i in range(len(direction)):
    if direction[i] == 'N':
        Dtemp[0] = D[1]
        Dtemp[1] = D[5]
        Dtemp[2] = D[2]
        Dtemp[3] = D[3]
        Dtemp[4] = D[0]
        Dtemp[5] = D[4]
    elif direction[i] == 'E':
        Dtemp[0] = D[3]
        Dtemp[1] = D[1]
        Dtemp[2] = D[0]
        Dtemp[3] = D[5]
        Dtemp[4] = D[4]
        Dtemp[5] = D[2]
    elif direction[i] =='S':
        Dtemp[0] = D[4]
        Dtemp[1] = D[0]
        Dtemp[2] = D[2]
        Dtemp[3] = D[3]
        Dtemp[4] = D[5]
        Dtemp[5] = D[1]
    elif direction[i] =='W':
        Dtemp[0] = D[2]
        Dtemp[1] = D[1]
        Dtemp[2] = D[5]
        Dtemp[3] = D[0]
        Dtemp[4] = D[4]
        Dtemp[5] = D[3]
    D=Dtemp
    Dtemp=[0,0,0,0,0,0]
print(label[D[0]])

