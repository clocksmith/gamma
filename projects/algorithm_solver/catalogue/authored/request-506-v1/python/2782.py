# Original implementation. Contract: https://leetcode.com/problems/number-of-unique-categories/
def solve(n,categoryHandler):
    if isinstance(categoryHandler,list):
        categories=categoryHandler
        same=lambda a,b:categories[a]==categories[b]
    else:same=categoryHandler.haveSameCategory
    representatives=[]
    for i in range(n):
        if not any(same(i,j) for j in representatives):representatives.append(i)
    return len(representatives)
