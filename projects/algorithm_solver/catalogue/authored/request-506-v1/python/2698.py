# Original candidate. Contract: https://leetcode.com/problems/find-the-punishment-number-of-an-integer/
def solve(n):
    answer=0
    for x in range(1,n+1):
        s=str(x*x)
        def match(i,remaining):
            if i==len(s):return remaining==0
            value=0
            for j in range(i,len(s)):
                value=value*10+int(s[j])
                if value>remaining:break
                if match(j+1,remaining-value):return True
            return False
        if match(0,x):answer+=x*x
    return answer
