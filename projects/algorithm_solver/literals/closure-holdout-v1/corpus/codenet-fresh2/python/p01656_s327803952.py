import bisect
n,q=map(int,input().split())
year=[1]
name=["kogakubu10gokan"]
for i in range(n):
    ye,na=map(str,input().split())
    year.append(int(ye))
    name.append(na)
b=bisect.bisect_left(year,q+1)
print(name[b-1])
