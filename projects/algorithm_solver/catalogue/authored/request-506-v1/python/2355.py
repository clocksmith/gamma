# Original implementation. Contract: https://leetcode.com/problems/maximum-number-of-books-you-can-take/
def solve(books):
    stack=[];dp=[0]*len(books)
    for i,b in enumerate(books):
        while stack and books[stack[-1]]-stack[-1]>=b-i:stack.pop()
        j=stack[-1] if stack else -1;length=min(i-j,b)
        dp[i]=(b+b-length+1)*length//2+(dp[j] if j>=0 else 0);stack.append(i)
    return max(dp)
