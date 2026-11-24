n = int(input())
a = []
for i in range(n):
  a.append(input())
for i in range(n):
  k = list(a[i])
  k.sort()
  k = ''.join(k)
  a[i] = k
a.sort()
k = 1
s = 0
for i in range(n-1):
  if a[i] == a[i+1]:
    k += 1
  else:
    s += k*(k-1)/2
    k = 1
s += k*(k-1)/2
print(int(s))