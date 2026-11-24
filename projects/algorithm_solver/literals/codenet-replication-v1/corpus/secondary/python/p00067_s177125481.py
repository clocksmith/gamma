while True:
    c=0
    islands=[]
    islandsID=[]
    ID=0

    def dfs(row,col):
        global ID
        if 0<=row<12 and 0<=col<12:
            if islands[row][col]==1 and islandsID[row][col]==0:
                islandsID[row][col]=ID
                for dr, dc in [[0,1],[1,0],[0,-1],[-1,0]]:
                    dfs(row+dr,col+dc)

    for i in range(12):
        islands.append(list(int(k) for k in input()))
    for _ in range(12):
        islandsID.append([0 for i in range(12)])

    for i in range(12):
        for j in range(12):
            if islands[i][j]==1 and islandsID[i][j]==0:
                ID+=1
                dfs(i,j)
    print(ID)
    try:
        c=input()
    except:
        break
