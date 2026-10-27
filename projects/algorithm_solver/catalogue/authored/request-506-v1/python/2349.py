# Original candidate. Contract: https://leetcode.com/problems/design-a-number-container-system/
def solve(operations, arguments):
    import heapq
    current={};heaps={};out=[]
    for op,a in zip(operations,arguments):
        if op=='NumberContainers':current.clear();heaps.clear();out.append(None)
        elif op=='change':
            index,value=a;current[index]=value;heapq.heappush(heaps.setdefault(value,[]),index);out.append(None)
        elif op=='find':
            value=a[0];h=heaps.get(value,[])
            while h and current.get(h[0])!=value:heapq.heappop(h)
            out.append(h[0] if h else -1)
        else:raise ValueError('unknown operation')
    return out
