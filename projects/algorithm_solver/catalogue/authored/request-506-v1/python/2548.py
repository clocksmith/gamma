# Original candidate. Contract: https://leetcode.com/problems/maximum-price-to-fill-a-bag/
def solve(items, capacity):
    total=0.0
    for price,weight in sorted(items,key=lambda x:x[0]/x[1],reverse=True):
        used=min(capacity,weight);total+=price*used/weight;capacity-=used
        if not capacity:return total
    return -1
