import sys

readline = sys.stdin.buffer.readline

ns = lambda: readline().rstrip()
ni = lambda: int(readline().rstrip())
nm = lambda: map(int, readline().split())
nl = lambda: list(map(int, readline().split()))

def solve():
  s = [x - 97 for x in ns()]
  n = len(s)
  c = 0
  g = {0:0}
  for x in s:
    c ^= 1 << x
    y = g.get(c, n) + 1
    for i in range(26):
      y = min(y, g.get(c ^ (1 << i), n) + 1)
    g[c] = min(g.get(c, n), y)
  print(y)
  return

solve()
