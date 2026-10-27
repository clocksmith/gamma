# Original candidate. Contract: https://leetcode.com/problems/detect-squares/
def solve(operations, arguments):
    from collections import Counter
    points=Counter();out=[]
    for op,args in zip(operations,arguments):
        if op=='DetectSquares':points.clear();out.append(None)
        elif op=='add':points[tuple(args[0])]+=1;out.append(None)
        elif op=='count':
            x,y=args[0];answer=0
            for (a,b),count in points.items():
                if a!=x and abs(a-x)==abs(b-y):answer+=count*points[(a,y)]*points[(x,b)]
            out.append(answer)
        else:raise ValueError('unknown operation')
    return out
