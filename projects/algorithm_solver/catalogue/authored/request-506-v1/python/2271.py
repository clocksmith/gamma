# Original candidate. Contract: https://leetcode.com/problems/maximum-white-tiles-covered-by-a-carpet/
def solve(tiles, carpetLen):
    a=sorted(tiles);j=total=ans=0
    for i,(left,right) in enumerate(a):
        end=left+carpetLen
        while j<len(a) and a[j][1]<end:total+=a[j][1]-a[j][0]+1;j+=1
        ans=max(ans,total+(max(0,end-a[j][0]) if j<len(a) else 0))
        if j>i:total-=right-left+1
        else:j=i+1
    return ans
