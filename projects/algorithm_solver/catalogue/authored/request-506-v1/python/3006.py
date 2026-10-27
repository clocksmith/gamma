# Original candidate implementation. Contract: https://leetcode.com/problems/find-beautiful-indices-in-the-given-array-i/
def solve(s,a,b,k):
    aa=[i for i in range(len(s)-len(a)+1) if s.startswith(a,i)]
    bb=[i for i in range(len(s)-len(b)+1) if s.startswith(b,i)]
    result=[]; j=0
    for i in aa:
        while j<len(bb) and bb[j]<i-k: j+=1
        if j<len(bb) and bb[j]<=i+k: result.append(i)
    return result
