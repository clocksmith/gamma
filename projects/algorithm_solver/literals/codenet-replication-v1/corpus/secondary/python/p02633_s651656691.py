x = int(input())
for i in range(1, 361):
  if 360*i % x == 0:
    print(360*i//x)
    break
else:
  print(360)