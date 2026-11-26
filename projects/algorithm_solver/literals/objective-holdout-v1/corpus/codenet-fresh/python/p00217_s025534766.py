while True:
    n = int(input())
    if n == 0:
        break

    patients = []
    for _ in range(n):
        p, d1, d2 = map(int, input().split())
        patients.append((p, d1+d2))
    print(*max(patients, key=lambda x: x[1]))