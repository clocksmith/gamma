# Original candidate implementation. Contract: https://leetcode.com/problems/number-of-smooth-descent-periods-of-a-stock/
def solve(prices):
    answer = run = 0
    for i, price in enumerate(prices):
        run = run + 1 if i and prices[i-1] == price+1 else 1
        answer += run
    return answer
