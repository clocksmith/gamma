n, k = map(int, input().split())

num_list = list(range(1, n+1))
count = 0

if k % 2 == 1:
    count = (n // k) ** 3  

else:
    count = (n // k) ** 3  + ((n + k // 2) // k )** 3

print(count)