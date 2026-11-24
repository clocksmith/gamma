n = int(input())
if ((n % 1000) % 111 == 0) or ((n // 10) % 111 == 0):
    print('Yes')
else:
    print('No')