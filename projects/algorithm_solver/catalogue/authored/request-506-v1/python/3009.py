# Original candidate. Contract: https://leetcode.com/problems/maximum-number-of-intersections-on-the-chart/
def solve(y):
    events={}
    def add(lo,hi):
        events[lo]=events.get(lo,0)+1;events[hi+1]=events.get(hi+1,0)-1
    for a,b in zip(y,y[1:]):
        if a<b:add(2*a,2*b-1)
        else:add(2*b+1,2*a)
    add(2*y[-1],2*y[-1]);active=answer=0
    for x in sorted(events):active+=events[x];answer=max(answer,active)
    return answer
