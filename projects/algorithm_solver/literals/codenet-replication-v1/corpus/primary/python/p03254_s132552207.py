N, x = map(int, input().split())
a = list(map(int, input().split()))

i = 0
while len(a) > 0:
    if min(a) > x:
        break
    else:
        x -= min(a)
        a.remove(min(a))
        i += 1
if len(a) == 0:
    if x > 0:
        i -= 1
print(i)