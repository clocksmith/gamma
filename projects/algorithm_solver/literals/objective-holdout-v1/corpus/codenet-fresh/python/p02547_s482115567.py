n = int(input())
ds = []
for i in range(n):
  d_1, d_2 = map(int, input().split())
  ds.append((d_1, d_2))
for j in range(n-2):
  if ds[j][0] == ds[j][1] and ds[j+1][0] == ds[j+1][1] and ds[j+2][0] == ds[j+2][1]:
    print("Yes")
    exit()
print("No")