"""Original candidate for LeetCode 2117. Contract: https://leetcode.com/problems/abbreviating-the-product-of-a-range/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: Exact arbitrary-precision product; O((right-left+1)*B) bit-arithmetic upper bound, O(B) bits; B=product bit length"""
def solve(left,right):
    product=1
    for x in range(left,right+1):product*=x
    zeros=0
    while product%10==0:product//=10;zeros+=1
    if product<10**10:return str(product)+'e'+str(zeros)
    # Estimate then correct exactly, avoiding Python large-int string limit.
    digits=product.bit_length()*30103//100000+1
    power=10**(digits-1)
    while product<power:digits-=1;power//=10
    while product>=power*10:digits+=1;power*=10
    prefix=product//(10**(digits-5));suffix=product%100000
    return str(prefix)+'...'+str(suffix).zfill(5)+'e'+str(zeros)
