while True:
    try:
        hoge = input()
    except:
        break
    ans = "d"
    for i in range(3):
        if "ooo" == hoge[i*3:i*3+3] or "ooo" == hoge[i::3]:
            ans = "o"
            break
        elif "xxx" == hoge[i*3:i*3+3] or "xxx" == hoge[i::3]:
            ans = "x"
            break
    if hoge[0::4] == "ooo" or hoge[2:7:2] == "ooo":
        ans = "o"
    elif hoge[0::4] == "xxx" or hoge[2:7:2] == "xxx":
        ans = "x"
    print(ans)