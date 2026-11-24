# coding: utf-8
# Your code here!

s=input().split("BC")
s.pop()
ans = 0
now=0
#print(s)
for i in s:
    if "B" not in i and "C" not in i:
        now += len(i)
        ans += now
    else:
        x=i.rfind('B')
        y=i.rfind('C')
        now = len(i) - max(x,y) - 1
        ans += now
#    print(now,ans)

print(ans)