s = input()
t = input()

ans = [None for i in range(len(s))]
for i in range(len(s)):
    ans[i] = s[i]

for i in reversed(range(len(s)-len(t)+1)):
    flag = 0
    for j in range(len(t)):
        if s[i+j]!=t[j] and s[i+j]!="?":
            flag = 1
    if flag == 0:
        for j in range(len(t)):
            ans[i+j]=t[j]
        for j in range(len(s)):
            if ans[j]=="?":
                ans[j]="a"
        print("".join(ans))
        exit()

print("UNRESTORABLE")
