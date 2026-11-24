N = int(input())

INF = 10**20
max_Lx, max_Rx, max_UDx = -INF, -INF, -INF
min_Lx, min_Rx, min_UDx = INF, INF, INF
max_Uy, max_Dy, max_LRy = -INF, -INF, -INF
min_Uy, min_Dy, min_LRy = INF, INF, INF

for _ in range(N) :
    x, y, d = input().split()
    x, y = int(x), int(y)
    
    if d == 'L' :
        max_Lx = max(max_Lx, x)
        min_Lx = min(min_Lx, x)
        max_LRy = max(max_LRy, y)
        min_LRy = min(min_LRy, y)
    
    elif d == 'R' :
        max_Rx = max(max_Rx, x)
        min_Rx = min(min_Rx, x)
        max_LRy = max(max_LRy, y)
        min_LRy = min(min_LRy, y)
    
    elif d == 'U' :
        max_Uy = max(max_Uy, y)
        min_Uy = min(min_Uy, y)
        max_UDx = max(max_UDx, x)
        min_UDx = min(min_UDx, x)
    
    elif d == 'D':
        max_Dy = max(max_Dy, y)
        min_Dy = min(min_Dy, y)
        max_UDx = max(max_UDx, x)
        min_UDx = min(min_UDx, x)

def calc(t) :
    max_x = max(max_Lx-t, max_UDx, max_Rx+t)
    min_x = min(min_Lx-t, min_UDx, min_Rx+t)
    max_y = max(max_Dy-t, max_LRy, max_Uy+t)
    min_y = min(min_Dy-t, min_LRy, min_Uy+t)
    return (max_x - min_x) * (max_y - min_y)

schedule = [
    0, 
    max_UDx - max_Rx, max_Lx - max_UDx, (max_Lx - max_Rx) / 2,
    min_UDx - min_Rx, min_Lx - max_UDx, (min_Lx - min_Rx) / 2,
    max_LRy - max_Uy, max_Dy - max_LRy, (max_Dy - max_Uy) / 2,
    min_LRy - min_Uy, min_Dy - max_LRy, (min_Dy - min_Uy) / 2
]
min_diff = INF

for t in schedule :
    if 0 <= t < INF / 10 :
        min_diff = min(min_diff, calc(t))
    
print(min_diff)