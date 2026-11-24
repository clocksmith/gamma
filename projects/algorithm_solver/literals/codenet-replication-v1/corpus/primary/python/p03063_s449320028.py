N = int(input())
S = input()
whitecount = [0 for i in range(N+1)]
for i in range(N):
    if S[i] == ".":
        whitecount[i+1] = whitecount[i] + 1
    else:
        whitecount[i+1] = whitecount[i]
ans = 1000000
for i in range(N+1):
    anstemp = i - whitecount[i] + (whitecount[-1] - whitecount[i])
    ans = min(anstemp, ans)
print(ans)
