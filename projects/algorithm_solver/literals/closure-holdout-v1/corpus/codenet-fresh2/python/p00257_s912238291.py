def search(x, visited, edges):
  if visited[x]:
    return

  visited[x] = True
  for to in edges[x]:
    search(to, visited, edges)

def main():
  while True:
    m = int(input())
    if m == 0:
      break
    n = int(input())
    mp = [0] + [int(input()) for _ in range(n)] + [0]
    visited = [False] * (n + 2)
    rev_visited = [False] * (n + 2)
    edges = [[] for _ in range(n + 2)]
    rev_edges = [[] for _ in range(n + 2)]
    for i in range(n + 2):
      for j in range(1, m + 1):
        nex = i + j
        nex = min(nex, n + 1)
        nex += mp[nex]
        nex = min(nex, n + 1)
        nex = max(nex, 0)
        edges[i].append(nex)
        rev_edges[nex].append(i)
  
    search(0, visited, edges)
    search(n + 1, rev_visited, rev_edges)
    for node in range(n + 1):
      if visited[node] and not rev_visited[node]:
        print("NG")
        break
    else:
      print("OK")

main()
