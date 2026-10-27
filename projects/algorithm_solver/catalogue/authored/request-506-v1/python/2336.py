# Original candidate. Contract: https://leetcode.com/problems/smallest-number-in-infinite-set/
def solve(operations, arguments):
    missing=set();out=[]
    for op,a in zip(operations,arguments):
        if op=='SmallestInfiniteSet':missing.clear();out.append(None)
        elif op=='addBack':missing.discard(a[0]);out.append(None)
        elif op=='popSmallest':
            x=1
            while x in missing:x+=1
            missing.add(x);out.append(x)
        else:raise ValueError('unknown operation')
    return out
