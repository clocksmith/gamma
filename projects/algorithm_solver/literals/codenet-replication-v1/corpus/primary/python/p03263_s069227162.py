H, W = map(int, input().split( ))

a = []

for _ in range(H):
    A = list(map(int, input().split( )))
    a.append(A)

i = 0
j = 0
cnt = 0
ans = []
for h in range(H):
    for w in range(W):
        if a[h][w]%2 ==1:
            if w != W-1:
                cnt += 1
                ans.append([h+1,w+1,h+1,w+2])
                a[h][w] -= 1
                a[h][w+1] += 1
            else:
                if h != H-1:
                    cnt += 1
                    ans.append([h+1,w+1, h+2, w+1])
                    a[h][w] -= 1
                    a[h+1][w] += 1
print(cnt)
for i in range(len(ans)):
    print(*ans[i])
                    
            