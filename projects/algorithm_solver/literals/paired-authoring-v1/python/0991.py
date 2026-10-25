class Solution:
    def brokenCalc(self, startValue, target):
        operations = 0
        while target > startValue:
            if target % 2 == 1:
                target += 1
            else:
                target //= 2
            operations += 1
        return operations + startValue - target
