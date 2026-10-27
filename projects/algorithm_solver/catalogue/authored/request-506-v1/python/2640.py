# Original candidate implementation. Contract: https://leetcode.com/problems/find-the-score-of-all-prefixes-of-an-array/
def solve(nums):
    answer=[]; largest=total=0
    for value in nums:
        largest=max(largest,value); total+=value+largest; answer.append(total)
    return answer
