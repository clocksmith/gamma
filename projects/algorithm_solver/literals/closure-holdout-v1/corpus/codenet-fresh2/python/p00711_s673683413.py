from collections import deque
d = [(1,0),(-1,0),(0,1),(0,-1)]
while 1:
    w,h = map(int, input().split())
    if w == h == 0:
        break
    s = [input() for i in range(h)]
    bfs_map = [[1 for i in range(w)] for j in range(h)]
    for y in range(h):
        for x in range(w):
            if s[y][x] == "@":
                ans = 1
                q = deque()
                q.append((y,x))
                bfs_map[y][x] = 0
                while q:
                    y, x = q.popleft()
                    for dy,dx in d:
                        y_ = y+dy
                        x_ = x+dx
                        if 0 <= y_ < h and 0 <= x_ < w:
                            if bfs_map[y_][x_] and s[y_][x_] == ".":
                                ans += 1
                                bfs_map[y_][x_] = 0
                                q.append((y_,x_))
                print(ans)
                break

