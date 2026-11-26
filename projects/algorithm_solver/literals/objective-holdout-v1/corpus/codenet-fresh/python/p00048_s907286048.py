import sys
a,b,o,ab = 0,0,0,0
for line in sys.stdin.readlines():
  w = float(line)
  if w <= 48:
    print('light fly')
  elif 48 < w <= 51:
    print('fly')
  elif 51 < w <= 54:
    print('bantam')
  elif 54 < w <= 57:
    print('feather')
  elif 57 < w <= 60:
    print('light')
  elif 60 < w <= 64:
    print('light welter')
  elif 64 < w <= 69:
    print('welter')
  elif 69 < w <= 75:
    print('light middle')
  elif 75 < w <= 81:
    print('middle')
  elif 81 < w <= 91:
    print('light heavy')
  else:
    print('heavy')