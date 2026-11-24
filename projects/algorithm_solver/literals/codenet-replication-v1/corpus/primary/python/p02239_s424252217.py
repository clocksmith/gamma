n = int(input())
adjlis = []
for _ in range(n):
    lis=list(map(int,input().split()))
    adjlis.append(lis[2:])

visited = [False]*n
dislis = [n+1]*n
Q = [[1,0]]

def pull():
    return Q.pop(0)

def push(x):
    Q.append(x)

while len(Q)>0:
    cur = pull()
    curpoint = cur[0]
    count = cur[1]
    if not visited[curpoint-1]:
        visited[curpoint-1]=True
        dislis[curpoint-1] = count
        for i in adjlis[curpoint-1]:
            push([i,count+1])


for i in range(n):
    if dislis[i]==n+1:
        dislis[i] = -1
    print(i+1,dislis[i])
            
