def main():
    n = int(input())
    s = input()
    divider = pow(10, 9) + 7
    if s[0] == "W" or s[2 * n - 1] == "W":
        print(0)
        return
    flag = True
    cnt = 1
    ret = 1
    for i in range(1, 2 * n):
        if s[i - 1] == s[i]:
            flag = not flag
        if flag:
            cnt += 1
        else:
            ret *= cnt
            ret %= divider
            cnt -= 1
    if not cnt == 0:
        print(0)
        return
    for i in range(n):
        ret *= i + 1
        ret %= divider
    print(ret)
    return


if __name__ == "__main__":
    main()
