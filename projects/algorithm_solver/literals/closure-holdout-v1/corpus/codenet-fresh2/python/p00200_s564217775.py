from heapq import heappop as hpop
from heapq import heappush as hpush

def main():
  
  while True:
    n, m = map(int, input().split())
    
    if not n:
      break
    
    cost_edges = [[] for _ in range(m)]
    time_edges = [[] for _ in range(m)]
  
    for _ in range(n):
      a, b, c, t = map(int, input().split())
      cost_edges[a - 1].append((c, b - 1))
      cost_edges[b - 1].append((c, a - 1))
      time_edges[a - 1].append((t, b - 1))
      time_edges[b - 1].append((t, a - 1))
    
    k = int(input())
  
    for _ in range(k):
      start, goal, r = map(int ,input().split())
      start -= 1
      goal -= 1
      
      if r:
        edges = time_edges
      else:
        edges = cost_edges
  
      que = [(0, start)]
      visited = [False for _ in range(m)]
      
      while True:
        score, station = hpop(que)
        visited[station] = True
        
        if station == goal:
          print(score)
          break
  
        for c, to_station in edges[station]:
          if not visited[to_station]:
            hpush(que, (score + c, to_station))

main()
