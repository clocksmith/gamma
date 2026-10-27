# Original candidate. Contract: https://leetcode.com/problems/maximum-number-of-people-that-can-be-caught-in-tag/
def solve(team, dist):
    a=[i for i,x in enumerate(team) if x];b=[i for i,x in enumerate(team) if not x];i=j=answer=0
    while i<len(a) and j<len(b):
        if abs(a[i]-b[j])<=dist:answer+=1;i+=1;j+=1
        elif a[i]<b[j]:i+=1
        else:j+=1
    return answer
