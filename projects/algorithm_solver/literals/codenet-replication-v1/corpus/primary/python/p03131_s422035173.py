K, A, B = map(int, input().split())
if B - A <= 2 or K <= A:
    print(K + 1)
else:
    K -= A + 1
    if K % 2:
        print(B + (B - A) * ((K - 1) // 2) + 1)
    else:
        print(B + (B - A) * (K // 2))