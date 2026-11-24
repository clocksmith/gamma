while True:
  t = int(input())
  if t == 0:
    break
    
  n = int(input())
  
  ans = 0
  for _ in range(n):
    s, f = map(int, input().split())
    ans += f - s
    
  if ans >= t:
    print('OK')
  else:
    print(t - ans)
