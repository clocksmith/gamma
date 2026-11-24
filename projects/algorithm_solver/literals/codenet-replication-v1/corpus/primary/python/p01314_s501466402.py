

while True:

    N = int(input())

    if N == 0:
        break

    ans = 0

    lis = [0]

    for i in range(1000):

        lis.append(lis[-1] + i+1)

    for i in range(1001):

        for j in range(i-1):

            if lis[i] - lis[j] == N:
                ans += 1

    print (ans)

