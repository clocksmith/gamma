
#input
#N = list(map(int,input().split()))
#H = list(map(int,input().split()))
[N, K] = list(map(int,input().split()))
S = str(input())
tmp = 1
list_S = []
for i in range(N):
    if i == N-1:
        list_S.append(tmp)
        break
    if S[i] != S[i+1]:
        list_S.append(tmp)
        tmp = 1
    else:
        tmp += 1
M = len(list_S)+1
list_S = list_S + [0]*(2*K+5)
if S[0] == "0":
    list_S = [0] + list_S
    
tmp = sum(list_S[0:2*K + 1])
ans = sum(list_S[0:2*K + 1])
for i in range(0,M+2,2):
    tmp = tmp - list_S[i] -list_S[i+1]
    tmp = tmp + list_S[i+2*K+1] + list_S[i+2*K+2]
    if tmp > ans:
        ans = tmp
print(ans)
    