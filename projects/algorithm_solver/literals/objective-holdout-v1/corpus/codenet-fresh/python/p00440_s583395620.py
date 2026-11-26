anss = []
flag = False
def main():
    N, K = [int(i) for i in input().split()]
    if N == K == 0:
        global flag
        flag = True
        return
    A = [int(input()) for _ in range(K)]
    A.sort()
    zero = False
    if A[0] == 0:
        zero = True
    prev = -1
    last_island = -1
    current_streak = 0
    ans = 0
    for a in A:
        if prev == -1 or a == prev + 1:
            current_streak += 1
        elif zero == True and a == prev + 2:
            last_island = current_streak
            current_streak = 1
        else:
            last_island = -1
            current_streak = 1
        ans = max(current_streak + last_island + 1, ans)
        prev = a
    global anss
    anss.append(ans)
while not flag:
    main()
for a in anss:
    print(a)
