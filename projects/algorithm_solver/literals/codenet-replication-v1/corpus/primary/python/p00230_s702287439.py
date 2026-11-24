from collections import deque

def fix(alst, blst, floar, buil, n):
  if buil == 0:
    lst = alst
  else:
    lst = blst
  
  if lst[floar] == 0:
    return floar
  if lst[floar] == 1:
    while floar + 1 < n and lst[floar + 1] == 1:
      floar += 1
    return floar
  if lst[floar] == 2:
    while lst[floar] == 2:
      floar -= 1
    return floar 

def search(alst, blst, n):
  que = deque()
  #(cost, floar, buil)
  init_floar_a = fix(alst, blst, 0, 0, n)
  init_floar_b = fix(alst, blst, 0, 1, n)
  if n - 1 in (init_floar_a, init_floar_b):
    print(0)
    return
  que.append((0, init_floar_a, 0))
  que.append((0, init_floar_b, 1))
  dic = {}
  dic[(0, init_floar_a)] = 0
  dic[(0, init_floar_b)] = 0
  while que:
    total, floar, buil = que.popleft()
    next_buil = (buil + 1) % 2
    for i in range(3):
      if floar + i >= n:
        break
      to = fix(alst, blst, floar + i, next_buil, n)
      if to == n - 1:
        print(total + 1)
        return
      if (to, next_buil) not in dic:
        dic[(to, next_buil)] = total + 1
        que.append((total + 1, to, next_buil))
  print("NA")


while True:
  n = int(input())
  if n == 0:
    break
  alst = list(map(int, input().split()))
  blst = list(map(int, input().split()))
  search(alst, blst, n)
  
