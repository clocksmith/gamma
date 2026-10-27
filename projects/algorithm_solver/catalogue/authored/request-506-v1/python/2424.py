# Original candidate. Contract: https://leetcode.com/problems/longest-uploaded-prefix/
def solve(operations, arguments):
    uploaded=set();prefix=0;out=[]
    for op,a in zip(operations,arguments):
        if op=='LUPrefix':uploaded.clear();prefix=0;out.append(None)
        elif op=='upload':
            uploaded.add(a[0])
            while prefix+1 in uploaded:prefix+=1
            out.append(None)
        elif op=='longest':out.append(prefix)
        else:raise ValueError('unknown operation')
    return out
