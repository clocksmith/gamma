import sys
f = sys.stdin


while True:
    n = int(f.readline())
    if n == -1:
        break
    location = 1 + 0j
    for i in range(1, n):
        location += (location * 1j) / abs(location)
    print('{:.2f}'.format(location.real))
    print('{:.2f}'.format(location.imag))
    