# Original candidate. Contract: https://leetcode.com/problems/count-pairs-that-form-a-complete-day-ii/
def solve(hours):
    count=[0]*24;answer=0
    for x in hours:answer+=count[-x%24];count[x%24]+=1
    return answer
