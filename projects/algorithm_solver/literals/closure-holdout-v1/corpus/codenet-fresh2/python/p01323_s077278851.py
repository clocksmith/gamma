t = int(input())
vec = ((1, 0), (0, -1), (-1, 0), (0, 1))
for _ in range(t):
  def check(x, y, lst, checked):
    checked[y][x] = False
    color = mp[y][x]
    for dx, dy in vec:
      nx, ny = x + dx, y + dy
      if color == mp[ny][nx] and checked[ny][nx] == None:
        lst.append((nx, ny))
        check(nx, ny, lst, checked)
  
  mp = [list("X" * 8)] + [list("X" + input() + "X") for _ in range(12)] + [list("X" * 8)]
  cnt = 0
  
  while True:
    checked = [[None] * 8 for _ in range(14)]
    for y in range(1, 13):
      for x in range(1, 7):
        if mp[y][x] in ("O", ".", "X"):
          checked[y][x] = False
        elif checked[y][x] == None:
          lst = [(x, y)]
          check(x, y, lst, checked)
          length = len(lst)
          if length < 4:continue
          for nx, ny in lst:
            checked[ny][nx] = True
  
    if not any(any(lst) for lst in checked):
      break
    
    for y in range(1, 13):
      for x in range(1, 7):
        if mp[y][x] == "O":
          for dx, dy in vec:
            nx, ny = x + dx, y + dy
            if mp[ny][nx] != "O" and checked[ny][nx]:
              checked[y][x] = True
    
    for y in range(1, 13):
      for x in range(1, 7):
        if checked[y][x]:
          mp[y][x] = "."
  
    for x in range(1, 7):
      s = ""
      for y in range(12, 0, -1):
        s = mp[y][x] + s
      s = s.replace(".", "")
      s = "." * (12 - len(s)) + s
      for y in range(12, 0, -1):
        mp[y][x] = s[y - 1]
  
    cnt += 1
  
  print(cnt)
