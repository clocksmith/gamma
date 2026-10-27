"""Original candidate for LeetCode 2166. Contract: https://leetcode.com/problems/design-bitset/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows Bitset class-call arrays.
Complexity: O(1) operations except O(size) toString; O(size+output) space"""
def solve(operations,arguments):
    size=arguments[0][0];bits=[0]*size;flipped=0;ones=0;out=[None]
    for op,a in zip(operations[1:],arguments[1:]):
        result=None
        if op in ('fix','unfix'):
            i=a[0];want=int(op=='fix');old=bits[i]^flipped
            if old!=want:bits[i]^=1;ones+=1 if want else -1
        elif op=='flip':flipped^=1;ones=size-ones
        elif op=='all':result=ones==size
        elif op=='one':result=ones>0
        elif op=='count':result=ones
        elif op=='toString':result=''.join(str(b^flipped) for b in bits)
        out.append(result)
    return out
