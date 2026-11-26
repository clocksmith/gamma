while True:
    s = input()
    if s == '0':
        break
    ans = 0
    for item in s:
        ans += int(item)
    print(ans)


