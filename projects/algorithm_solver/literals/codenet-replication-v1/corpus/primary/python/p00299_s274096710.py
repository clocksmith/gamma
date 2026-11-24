import sys
import re
import math
import itertools
def create_edge(fr,to,weight,si):
    edges = []
    if si == '-':
        edges.append((fr,to,weight if to else 0))
        edges.append((to,fr,0))
    else:
        edges.append((to,fr,-weight))
    return edges
#????????????????????´???-1?????????
def bellmanford(edges, length):
    start_vertex = 0
    
    distance = [float('inf')] * length
    distance[start_vertex] = 0
    
    for i in range(length):
        for fr, to, weight in edges:
            if distance[to] > distance[fr] + weight:
                distance[to] = distance[fr] + weight

    for fr, to, weight in edges:
        if distance[to] > distance[fr] + weight:
           return -1
    if min(distance[1:]) < 0:
        return -1
    return max(distance)
f = sys.stdin


n,c = map(int, f.readline().split())

p = re.compile('(\d+)(\D+)(\d+)(\D+)(\d+)')
constraints = [p.match(line).groups() for line in f]

fixed_edges = []
floating_edges = []
for ai, oi, bi, si, di in constraints:
    fr,to,weight = int(ai) - 1,int(bi) - 1,int(di)

    if oi == '*':
        if fr and to:
            floating_edges.append((create_edge(fr,to,weight,si),create_edge(to,fr,weight,si)))
            continue
        oi = '<=' if fr < to else '>='

    if oi == '>=':
        fr, to = to, fr
    
    fixed_edges.extend(create_edge(fr,to,weight,si))
distance = []
for edges in itertools.product(*floating_edges):
    distance.append(bellmanford(fixed_edges + [y for x in edges for y in x], n))
print(max(distance))