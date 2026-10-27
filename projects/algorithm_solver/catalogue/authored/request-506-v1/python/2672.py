# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-adjacent-elements-with-the-same-color/
def solve(n, queries):
    colors=[0]*n; answer=[]; pairs=0
    for i,c in queries:
        for j in (i-1,i+1):
            if 0<=j<n:
                pairs -= int(colors[i]!=0 and colors[i]==colors[j])
                pairs += int(c==colors[j])
        colors[i]=c; answer.append(pairs)
    return answer
