class ans:
  def __init__(self):
    self.N, self.A, self.B, self.C = map(int,input().split())
    self.L = [int(input()) for _ in range(self.N)]
    print(self.dfs(0, 0, 0, 0))
    exit()

  def dfs(self, x, a, b, c):
    if(x == self.N):
      if(min(a, b, c) > 0):
        return abs(a-self.A)+abs(b-self.B)+abs(c-self.C) - 30
      else:
        return 1e9+7
    ret0 = self.dfs(x+1, a, b, c)
    ret1 = self.dfs(x+1, a+self.L[x], b, c) + 10
    ret2 = self.dfs(x+1, a, b+self.L[x], c) + 10
    ret3 = self.dfs(x+1, a, b, c+self.L[x]) + 10
    return min(ret0, ret1, ret2, ret3)

ans()