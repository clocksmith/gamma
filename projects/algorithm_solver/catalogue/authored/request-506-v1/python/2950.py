# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-divisible-substrings/
def solve(word):
    # Explicit keypad groups: ab,cde,fgh,ijk,lmn,opq,rst,uvw,xyz.
    values=[(ord(c)-97+1)//3+1 for c in word]
    answer=0
    for mean in range(1,10):
        prefix=0;seen={0:1}
        for value in values:
            prefix+=value-mean;answer+=seen.get(prefix,0);seen[prefix]=seen.get(prefix,0)+1
    return answer
