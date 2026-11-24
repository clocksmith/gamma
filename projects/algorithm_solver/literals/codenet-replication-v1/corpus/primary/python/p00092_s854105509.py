while True:
  n = int(input())
  if not n:
    break
  mp = []
  for _ in range(n):
    lst = list(input())
    cum = []
    acc = 0
    for i in lst:
      if i == ".":
        acc += 1
      else:
        acc = 0
      cum.append(acc)
    mp.append(cum)
  mp.append([-1] * n)
  ans = 0
  
  for i in range(n):
    stack = []
    for j in range(n + 1):
      score = mp[j][i]
      if not stack:
        stack.append((score, j))
      else:
        last_score, last_ind = stack[-1][0], stack[-1][1]
        if score > last_score:
          stack.append((score, j))
        
        elif score == last_score:
          continue
        
        else:
          while stack != [] and stack[-1][0] >= score:
            last_score, last_ind = stack.pop()
            ans = max(ans, min(last_score, j - last_ind))
          stack.append((score, last_ind))
  
  print(ans)
