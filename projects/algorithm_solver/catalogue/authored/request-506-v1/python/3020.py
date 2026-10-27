# Original candidate. Contract: https://leetcode.com/problems/find-the-maximum-number-of-elements-in-subset/
def solve(nums):
    from collections import Counter
    count=Counter(nums);ones=count.pop(1,0);answer=ones if ones%2 else ones-1
    for x in count:
        length=0;y=x
        while count.get(y,0)>=2:length+=2;y*=y
        length+=1 if count.get(y,0) else -1
        answer=max(answer,length)
    return max(1,answer)
