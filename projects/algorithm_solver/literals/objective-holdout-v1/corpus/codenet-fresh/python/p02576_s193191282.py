n, x, t = map(int, input().split())

kaisuu = n // x
if n % x != 0:
    kaisuu += 1
print(t*kaisuu)