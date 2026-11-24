X = list(map(int, input().split()))
for i in range(5):
    if X[i] == 0:
        print(i+1)
        exit()
