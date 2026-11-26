s = input()
q = [0,0,0]
for i in s:
    if i == 'a':
        q[0] += 1
    elif i == 'b':
        q[1] += 1
    else:
        q[2] += 1

if max(q) - min(q) > 1:
    print('NO')
else:
    print('YES')