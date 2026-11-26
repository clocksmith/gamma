n = int(input())

t_list = [int(i) for i in input().split()]
t_sum = sum(t_list)

m = int(input())

for i in range(m):
    p, x = map(int, input().split())
    time = t_sum - t_list[p-1] + x
    print(time)
