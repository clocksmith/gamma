flag = True
while True:
    n = int(input())
    if n == 0: break
    answer = {}
    for _ in range(n):
        result = input().split()
        country = result[0]
        win, lose, draw = map(int, result[1:])
        score = win * 3 + draw
        answer[country] = score
    if flag:
        flag = False
    else:
        print()
    for c, s in sorted(answer.items(), key=lambda x: -x[1]):
        print(c + ',' + str(s))
    
