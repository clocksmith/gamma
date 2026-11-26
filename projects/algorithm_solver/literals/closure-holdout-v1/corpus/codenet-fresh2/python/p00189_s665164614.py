INF = float('inf')
TOWN_NUM = 10

while True:
    way_num = int(input())
    if way_num == 0:
        break

    table = [[INF for i in range(TOWN_NUM)] for j in range(TOWN_NUM)]

    for _ in range(way_num):
        a,b,c = [int(i) for i in input().split()]
        table[a][b] = c
        table[b][a] = c

    for k in range(TOWN_NUM):
        for i in range(TOWN_NUM):
            for j in range(TOWN_NUM):
                if table[i][j] > table[i][k] + table[k][j]:
                    table[i][j] = table[i][k] + table[k][j]

    answer = INF
    answer_id = 0
    for i in range(TOWN_NUM):
        tmp = 0
        flag = False
        for j in range(TOWN_NUM):
            if table[i][j] < INF and i != j:
                tmp = tmp + table[i][j]
                flag = True
        if tmp < answer and flag:
            answer = tmp
            answer_id = i

    print(answer_id, answer)
