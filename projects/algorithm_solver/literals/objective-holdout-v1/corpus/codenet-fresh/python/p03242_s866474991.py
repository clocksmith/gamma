import math

n = input()
ans = ""
for i in n:
    if i == "1":
        ans += "9"
    else:
        ans += "1"
print(ans)