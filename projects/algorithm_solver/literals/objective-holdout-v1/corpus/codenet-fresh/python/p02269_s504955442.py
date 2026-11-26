n = int(input())
d = {}
for i in range(n):
    cmd, string = input().split()
    if cmd == "insert":
        d[string] = True
    else:
        try:
            if d[string]:
                print("yes")
        except:
            print("no")
