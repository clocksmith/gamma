import datetime

while True:
  y1, m1, d1, y2, m2, d2 = map(int, input().split())
  if y1 < 0 or m1 < 0 or d1 < 0 or y2 < 0 or m2 < 0 or d2 < 0:
    break

  D1 = datetime.datetime(y1, m1, d1)
  D2 = datetime.datetime(y2, m2, d2)
  dD = D2 - D1
  print(dD.days)
