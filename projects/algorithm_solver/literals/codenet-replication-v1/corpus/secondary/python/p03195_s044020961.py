n = int(input())
A_list = [int(input()) for _ in range(n)]
for a in A_list:
    if a % 2 == 1:
        print('first')
        exit()
print('second')