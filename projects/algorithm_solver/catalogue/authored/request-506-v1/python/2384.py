# Original candidate implementation. Contract: https://leetcode.com/problems/largest-palindromic-number/
def solve(num):
    counts = [num.count(str(i)) for i in range(10)]
    left = ''.join(str(i) * (counts[i]//2) for i in range(9,0,-1))
    if left:
        left += '0' * (counts[0]//2)
    middle = next((str(i) for i in range(9,-1,-1) if counts[i]%2), '')
    return left + middle + left[::-1] if left or middle else '0'
