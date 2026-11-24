#キーエンス プログラミング コンテスト 2019 b
s=input()
ans=False
for x in range(len(s)):
    for y in range(x,len(s)):
        if (s[:x]+s[y:])=='keyence':
            ans=True
if ans:
    print('YES')
else:
    print('NO')