data = [[[0 for r in range(10)] for f in range(3)] for b in range(4)]
  
count = int(input())
  
for c in range(count):
    (b, f, r, v) = [int(x) for x in input().split()]
    data[b - 1][f - 1][r - 1] += v
  
for b in range(4):
    for f in range(3):
        for r in range(10):
            print('',data[b][f][r], end='')
        print()
    if b < 3:
        print('#' * 20)