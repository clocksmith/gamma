import sys
readline = sys.stdin.readline

def main():
  N = int(readline())
  Sp = []
  Sm = []
  total = 0
  bm = 0
  for i in range(N):
    l = readline().strip()
    b = 0
    h = 0
    for j in range(len(l)):
      if l[j] == '(':
        h += 1
      else:
        h -= 1
      b = min(b, h)
    if h == 0 and b != 0:
      bm = min(bm, b)
    elif h > 0:
      Sp.append([b, h])
    elif h < 0:
      Sm.append([b-h, -h])
    total += h
  Sp.append([bm, 0])
  if total != 0:
    print('No')
    exit()
  Sp.sort(key=lambda x:x[0], reverse=True)
  p = check(Sp)
  if p < 0:
    print('No')
    exit()
  Sm.sort(key=lambda x:x[0], reverse=True)
  m = check(Sm)
  if m < 0:
    print('No')
    exit()
  print('Yes')

def check(S):
  h = 0
  for i in range(len(S)):
    if h + S[i][0] < 0:
      return -1
    else:
      h += S[i][1]
  return h

if __name__ == '__main__':
  main()