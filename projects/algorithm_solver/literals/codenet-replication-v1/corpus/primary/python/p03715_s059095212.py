H, W = map(int, input().split())
ans = 10**10
for i in range(1,H-1):
    h2 = (i+H)//2
    s1 = W*i
    s2 = W*(h2-i)
    s3 = W*(H-h2)
    tmp = max(s1,s2,s3) - min(s1,s2,s3)
    ans = min(tmp, ans)
    w = W//2
    s2 = (H-i) * w
    s3 = (H - i) * (W-w)
    tmp = max(s1,s2,s3) - min(s1,s2,s3)
    ans = min(tmp, ans)
for i in range(1,W):
    w2 = (W + i)//2
    s1 = i*H
    s2 = (w2-i)*H
    s3 = (W-w2)*H
    tmp = max(s1,s2,s3) - min(s1,s2,s3)
    ans = min(tmp, ans)

    h = H//2
    s2 = h * (W-i)
    s3 = (H-h) * (W-i)
    tmp = max(s1,s2,s3) - min(s1,s2,s3)
    ans = min(tmp, ans)
print(ans)