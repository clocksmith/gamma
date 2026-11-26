import sys
f = sys.stdin

while True:
    r, a = f.readline().strip().split()
    if r == '0':
        break
    hit = sum(1 for ri, ai in zip(r, a) if ri == ai)
    blow = sum(1 for ai in a if ai in r) - hit

    print(hit, blow)