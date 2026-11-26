sx, sy, tx, ty = map(int, input().split())

higth = ty - sy
width = tx - sx

ans = ''
ans += 'U' * higth
ans += 'R' * width
ans += 'D' * higth
ans += 'L' * width
ans += 'L' + 'U' * (higth + 1)
ans += 'R' * (width + 1) + 'D'
ans += 'R' + 'D' * (higth + 1)
ans += 'L' * (width + 1) + 'U'
print(ans)