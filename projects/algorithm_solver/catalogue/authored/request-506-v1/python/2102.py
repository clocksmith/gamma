"""Original candidate for LeetCode 2102. Contract: https://leetcode.com/problems/sequentially-ordinal-rank-tracker/
Development tests only; not admitted or independently qualified.
Batch class-call adapter. Coordinate compression sees future names but only past additions affect returned ranks; not a streaming class API.
Complexity: O(q log q) time, O(q) space"""
def solve(operations,arguments):
    ranked=sorted((-a[1],a[0]) for op,a in zip(operations,arguments) if op=='add')
    rank={name:i+1 for i,(_,name) in enumerate(ranked)};bit=[0]*(len(ranked)+1);out=[];query=0
    for op,a in zip(operations,arguments):
        if op=='add':
            i=rank[a[0]]
            while i<len(bit):bit[i]+=1;i+=i&-i
            out.append(None)
        elif op=='get':
            query+=1;k=query;i=0;step=1<<(len(ranked).bit_length()-1)
            while step:
                j=i+step
                if j<len(bit) and bit[j]<k:k-=bit[j];i=j
                step>>=1
            out.append(ranked[i][1])
        else:out.append(None)
    return out
