import sys

while True:
    L = int(input())
    if L == 0:
        break
    savings = 0
    a = [map(int, sys.stdin.readline().split()) for _ in [0]*12]
    for i, (M, N) in enumerate(a, start=1):
        savings += M - N
        if savings >= L:
            print(i)
            break
    else:
        print("NA")
