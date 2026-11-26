n = int(input())
for i in range(7):
  ch_l = 2**i
  ch_h = 2**(i+1)
  if ch_l <= n and n < ch_h:
    ans = 2**i
    break
print(ans)