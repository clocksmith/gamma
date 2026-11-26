x, n = list(map(int, input().split()))
p_list = list(map(int, input().split()))
if n == 0:
    print(x)
    exit()

i = 0
while True:
    x_i = x - i
    x_j = x + i

    if x_i not in p_list:
        print(x_i)
        exit()
    if x_j not in p_list:
        print(x_j)
        exit()

    i += 1
