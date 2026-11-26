s = list(input())

ll = len(s)

ans = 'AC'

if s[0] != 'A':
    ans = 'WA'

cnt = 0

for i in range(1, len(s)):
    if s[i].isupper():
        if i == 1 or i == ll - 1 or s[i] != 'C':
            ans = 'WA'
        cnt += 1

if cnt != 1:
    ans = 'WA'

print(ans)