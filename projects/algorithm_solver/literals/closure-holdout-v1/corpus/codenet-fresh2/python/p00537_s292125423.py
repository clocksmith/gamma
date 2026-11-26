import itertools

def main():
  n, m = map(int, input().split())
  plst = tuple(map(int, input().split()))
  abclst = [tuple(map(int, input().split())) for _ in range(n - 1)]
  
  sec = [0] * n
  for pi, pi1 in zip(plst, plst[1:]):
    p1, p2 = min(pi, pi1) - 1, max(pi, pi1) - 1
    sec[p1] += 1
    sec[p2] -= 1
  
  sec = tuple(itertools.accumulate(sec))
  
  ans = 0
  for i in range(n - 1):
    a, b, c = abclst[i]
    s = sec[i]
    ans += min(a * s, b * s + c)
  print(ans)
  
main() 
