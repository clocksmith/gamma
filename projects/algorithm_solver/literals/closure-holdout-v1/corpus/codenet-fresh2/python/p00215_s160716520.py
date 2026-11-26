from heapq import heappop,heappush
# from line_profiler import LineProfiler
def main():
    while(True):
        W, H = map(int,input().split())
        if not W: break
        B = float('inf')
        Bi = -1
        consequNodes = []
        monsterNodes = [[] for _ in range(5)]
        idx = 0
        for i in range(H):
            for j,a in enumerate(input()):
                if a == ".":
                    continue
                elif a == "S": 
                    consequNodes.append([i,j,idx,5])
                    startNode = [i,j,idx,5]
                    idx+=1
                elif a == "G":
                    consequNodes.append([i,j,idx,6])
                    goalNode = [i,j,idx,6]
                    idx+=1
                elif a != ".":
                    consequNodes.append([i,j,idx,int(a)-1])
                    monsterNodes[int(a)-1].append([i,j,idx])
                    idx+=1
        for z in range(5):
            consequNodes[startNode[2]][3] = z
            dist = [[float('inf')]*idx for _ in range(6)]
            dist[1][startNode[2]] = 0
            que = [(0,1,startNode[2],0)]
            reached = False
            while que:
                cst,numrep,nid,huristicCost = heappop(que)
                cst = int(cst)-int(huristicCost)
                if numrep == 5:
                    reached = True
                    cst += abs(consequNodes[nid][0]-goalNode[0]) + abs(consequNodes[nid][1]-goalNode[1])
                    break
                nxtmonster = (consequNodes[nid][3]+1)%5
                for nxty,nxtx,nxtid in monsterNodes[nxtmonster]:
                    tmpCost = dist[numrep][nid] + abs(nxty-consequNodes[nid][0]) + abs(nxtx-consequNodes[nid][1])
                    if tmpCost < dist[numrep+1][nxtid]:
                        dist[numrep+1][nxtid] = tmpCost
                        h = abs(nxty-goalNode[0]) + abs(nxtx-goalNode[1])
                        h *= 0.99
                        heappush(que,(tmpCost+h,numrep+1,nxtid,h))
            if reached and cst < B:
                B = cst
                Bi = z+1
        if Bi == -1:
            print("NA")
        else:
            print(Bi,B)

if __name__ == "__main__":
    # prf = LineProfiler()
    # prf.add_function(main)
    # prf.runcall(main)
    # prf.print_stats()
    main()
