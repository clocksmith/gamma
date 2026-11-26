while 1:
    m = int(input())
    if m == 0:
        break

    result = []
    for _ in range(m):
        datas = list(map(int, input().split()))
        student = datas.pop(0)

        score = 0
        frame = 1
        while 1:
            if frame == 10:
                while datas != []:
                    score += datas.pop(0)
                break

            first = datas.pop(0)
            if first == 10:
                score += 10 + datas[0] + datas[1]
            else:
                second = datas.pop(0)
                if first + second == 10:
                    score += 10 + datas[0]
                else:
                    score += first + second
            frame += 1

        result.append([student, score])

    result.sort()
    result = sorted(result, reverse=True, key=lambda x: x[1])
    for res in result:
        print(res[0], res[1])

