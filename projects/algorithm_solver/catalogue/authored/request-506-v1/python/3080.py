# Original candidate. Contract: https://leetcode.com/problems/mark-elements-on-array-by-performing-queries/
def solve(nums, queries):
    order=sorted(range(len(nums)),key=lambda i:(nums[i],i));seen=set();total=sum(nums);j=0;out=[]
    for index,k in queries:
        if index not in seen:seen.add(index);total-=nums[index]
        while k and j<len(order):
            i=order[j];j+=1
            if i not in seen:seen.add(i);total-=nums[i];k-=1
        out.append(total)
    return out
