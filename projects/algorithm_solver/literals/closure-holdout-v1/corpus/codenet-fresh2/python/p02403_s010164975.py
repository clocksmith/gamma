import sys

for line in sys.stdin:
    h, w = map(int, line.strip().split())
    if h == 0 and w == 0:
        break
    for _ in range(h):
        print('#' * w)

    print()

