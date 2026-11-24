def to_top_red(cube):
  c1, c2, c3, c4, c5, c6 = cube
  if c2 == "Red":
    c1, c2, c6, c5 = c2, c6, c5, c1
  elif c3 == "Red":
    c1, c4, c6, c3 = c3, c1, c4, c6
  elif c4 == "Red":
    c1, c4, c6, c3 = c4, c6, c3, c1
  elif c5 == "Red":
    c1, c5, c6, c2 = c5, c6, c2, c1
  elif c6 == "Red":
    c1, c2, c6, c5 = c6, c5, c1, c2
  return (c1, c2, c3, c4, c5, c6)

def regist(cube, cube_dic):
  c1, c2, c3, c4, c5, c6 = cube
  cube_dic[(c1, c2, c3, c4, c5, c6)] = True
  cube_dic[(c1, c4, c2, c5, c3, c6)] = True
  cube_dic[(c1, c3, c5, c2, c4, c6)] = True
  cube_dic[(c1, c5, c4, c3, c2, c6)] = True

while True:
  n = int(input())
  if n == 0:
    break

  cube_dic = {}
  ans = 0
  
  for _ in range(n):
    cube = to_top_red(input().split())
    if cube in cube_dic:
      ans += 1
    else:
      regist(cube, cube_dic)
  
  print(ans)
