S=input()
S=S[::-1]
cnt=["dream","dreamer","erase","eraser"]

for i in range(4):
  s=cnt[i]
  s=s[::-1]
  cnt[i]=s

while len(S):
  if S[:5]==cnt[0]:
    S=S[5:]
  elif S[:7]==cnt[1]:
    S=S[7:]
  elif S[:5]==cnt[2]:
    S=S[5:]
  elif S[:6]==cnt[3]:
    S=S[6:]
  else:
    break

if len(S):
  print("NO")
else:
  print("YES")
