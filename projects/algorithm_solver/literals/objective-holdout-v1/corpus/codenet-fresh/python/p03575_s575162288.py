def dfs(i):
    global nodes, flags
    if flags[i]:
        return
    flags[i]=True
    for n in nodes[i]:
        dfs(n)
    
    
    


line=input().split()
n=int(line[0])
m=int(line[1])

edges=[] #[a,b] for every edge
nodes=[[] for i in range (n)] #list of all neighbours for all nodes
flags=[False for i in range(n)]
for i in range(m):
    line=input().split()
    a=int(line[0])-1
    b=int(line[1])-1
    edges.append([a,b])
    nodes[a].append(b)
    nodes[b].append(a)
count=0
for i in range(m):
    a=edges[i][0]
    b=edges[i][1]
    nodes[a].remove(b)
    nodes[b].remove(a)
    dfs(0)
    bridge=False
    for j in range(n):
        if flags[j]==False:
            bridge = True
        flags[j]=False
    if bridge:
        count+=1
    nodes[a].append(b)
    nodes[b].append(a)
print(count)
