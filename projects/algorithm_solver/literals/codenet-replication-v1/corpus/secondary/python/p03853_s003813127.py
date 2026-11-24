H, W = map(int, input().split())
ret = ""
for _ in range(H):
    s = input()
    ret += s + "\n" + s + "\n"
print(ret)
