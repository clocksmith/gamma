# Original candidate. Contract: https://leetcode.com/problems/amount-of-new-area-painted-each-day/
def solve(paint):
    end=max(b for a,b in paint);parent=list(range(end+1))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    out=[]
    for a,b in paint:
        count=0;x=find(a)
        while x<b:count+=1;parent[x]=find(x+1);x=parent[x]
        out.append(count)
    return out
