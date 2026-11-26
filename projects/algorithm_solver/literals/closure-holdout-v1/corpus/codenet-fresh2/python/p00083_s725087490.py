start_data = [18680908, 19120730, 19261225, 19890108, 99999999]
era = ["pre-meiji", "meiji", "taisho", "showa", "heisei"]

while 1:
    try:
        y, m, d = map(int, input().split(" "))
        data = y * 10000 + m * 100 + d
        for i in range(5):
            if data < start_data[i]:
                if i is 0:
                    print(era[0])
                    break
                else:
                    print(era[i], data // 10000 - start_data[i - 1] // 10000 + 1, m, d)
                    break
    except:
        break

