from collections import Counter

n,k = map(int,input().split())
lst = list(map(int,input().split()))
typ = list(set(lst))

ans = 0
NumList = Counter(lst)
num = sorted(NumList.items(),key=lambda x:x[1])
for l in range(len(typ)-k):
    ans += num[l][1]
print(ans)
