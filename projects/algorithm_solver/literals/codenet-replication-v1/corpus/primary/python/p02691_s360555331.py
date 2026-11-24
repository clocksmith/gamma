n = int(input())
arr = list(map(int,input().split()))
addarr = [i+1+arr[i] for i in range(n)]
diffarr = [i+1-arr[i] for i in range(n)]

from collections import Counter
cnt = Counter([addarr[0]])
ans = 0

for i in range(1,n):
    tmp = diffarr[i]
    ans += cnt[tmp]
    cnt.update([addarr[i]])

print(ans)