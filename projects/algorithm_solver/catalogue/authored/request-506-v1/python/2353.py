"""Original candidate for LeetCode 2353. Contract: https://leetcode.com/problems/design-a-food-rating-system/
Development tests only; not admitted or independently qualified.
Explicit stateful adapter: solve(operations, arguments), constructor first, void results null; exact official method semantics.
Complexity: O((n+q) log(n+q)) amortized time, O(n+q) space"""
import heapq
def solve(operations,arguments):
    foods,cuisines,ratings=arguments[0];state={};heaps={}
    for f,c,r in zip(foods,cuisines,ratings):state[f]=(c,r);heapq.heappush(heaps.setdefault(c,[]),(-r,f))
    out=[None]
    for op,args in zip(operations[1:],arguments[1:]):
        if op=='changeRating':
            f,r=args;c=state[f][0];state[f]=(c,r);heapq.heappush(heaps[c],(-r,f));out.append(None)
        else:
            h=heaps[args[0]]
            while -h[0][0]!=state[h[0][1]][1]:heapq.heappop(h)
            out.append(h[0][1])
    return out
