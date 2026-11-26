def num():
    return int(input())
def nums():
    return list(map(int,input().split()))
"""
N = num()
A = nums()
print(A.index(min(A))+1)
"""
"""
N = num()
A =  set(nums())
print(len(A))
"""

def get_near_index(sorted_l,val,last):
    left = 0
    right = len(sorted_l) - 1
    while left <= right:
        mid = (right + left) // 2
        if sorted_l[mid] == val:
            return mid if last else mid
        elif sorted_l[mid] > val:
            right = mid -1
        else: 
            left = mid + 1
    return right if last else left 

N,Q = nums()
A = nums()
A.sort()
L,R = [],[]

for i in range(Q):
    li,ri = nums()
    L.append(li)
    R.append(ri)
for l,r in zip(L,R):
    l_idx = get_near_index(A,l,0)
    r_idx = get_near_index(A,r,1)
    print(r_idx-l_idx+1)
