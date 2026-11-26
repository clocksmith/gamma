N = int(input())
*A, = map(int, input().split())

def check(K):
    st = []
    for i, a in enumerate(A):
        #print(K, i, st, a)
        while st and a < st[-1][0]:
            st.pop()
        u = i > 0 and A[i-1] >= A[i]
        if not st:
            st.append([a, u])
            continue
        l = st[-1]
        if l[0] == a:
            l[1] += 1
            while st and l[1] == K:
                st.pop(); a -= 1
                if a == 0:
                    return 0
                if not st:
                    st.append([a, 1])
                    break
                l = st[-1]
                if l[0] == a:
                    l[1] += 1
                else:
                    st.append([a, 1])
                    break
            #print(l, st)
        else:
            st.append([a, u])
    #print(st)
    return 1

ok = 1
for i in range(N-1):
    if not A[i] < A[i+1]:
        ok = 0
if ok:
    print(1)
    exit(0)

left = 1; right = N+1
while left+1 < right:
    mid = (left + right) // 2
    if check(mid):
        right = mid
    else:
        left = mid
print(right)