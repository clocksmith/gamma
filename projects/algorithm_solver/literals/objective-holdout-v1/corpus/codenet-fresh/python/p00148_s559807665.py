import sys

for i in sys.stdin:
    p = int(i) % 39
    if p == 0:
        print("3C39")
    elif p < 10:
        print("3C0%d" %(p))
    else:
        print("3C%d" %(p))
