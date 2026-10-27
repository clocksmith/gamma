"""Original candidate for LeetCode 2613. Contract: https://leetcode.com/problems/beautiful-pairs/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time by closest-pair packing, O(n log n) conservative transient space"""
def solve(x,y):
    points=sorted((a,b,i) for i,(a,b) in enumerate(zip(x,y)));best=[10**18,(len(x),len(x))]
    def consider(a,b):
        d=abs(a[0]-b[0])+abs(a[1]-b[1]);pair=tuple(sorted((a[2],b[2])))
        if (d,pair)<tuple(best):best[:]=[d,pair]
    for i in range(1,len(points)):
        if points[i][:2]==points[i-1][:2]:consider(points[i-1],points[i])
    if best[0]==0:return list(best[1])
    def rec(ps):
        if len(ps)<=3:
            for i in range(len(ps)):
                for j in range(i):consider(ps[i],ps[j])
            return sorted(ps,key=lambda p:p[1])
        mid=len(ps)//2;cx=ps[mid][0];a=rec(ps[:mid]);b=rec(ps[mid:]);merged=[];i=j=0
        while i<len(a) or j<len(b):
            if j==len(b) or i<len(a) and a[i][1]<=b[j][1]:merged.append(a[i]);i+=1
            else:merged.append(b[j]);j+=1
        strip=[p for p in merged if abs(p[0]-cx)<=best[0]]
        for i,p in enumerate(strip):
            j=i-1
            while j>=0 and p[1]-strip[j][1]<=best[0]:consider(p,strip[j]);j-=1
        return merged
    rec(points);return list(best[1])
