w = int(input())
Ver = list(range(1, w+1))

n = int(input())

for i in range(n):
    j, k = map(int, input().split(','))

    temp = Ver[j-1]
    Ver[j-1] = Ver[k-1]
    Ver[k-1] = temp

for i in range(len(Ver)):
    print(Ver[i])