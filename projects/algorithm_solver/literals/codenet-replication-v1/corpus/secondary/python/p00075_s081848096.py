import sys

for line in sys.stdin:
  try:
    s, w, h = [float(i) for i in line.split(',')]
    if w / h**2 >= 25:
      print(int(s))
  except:
    break

