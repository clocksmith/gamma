# Original implementation. Contract: https://leetcode.com/problems/frequency-tracker/
from collections import Counter
class FrequencyTracker:
    def __init__(self):self.counts=Counter();self.frequencies=Counter()
    def change(self,number,delta):
        before=self.counts[number]
        if before:self.frequencies[before]-=1
        after=before+delta;self.counts[number]=after
        if after:self.frequencies[after]+=1
    def add(self,number):self.change(number,1)
    def deleteOne(self,number):
        if self.counts[number]:self.change(number,-1)
    def hasFrequency(self,frequency):return self.frequencies[frequency]>0
def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='FrequencyTracker':obj=FrequencyTracker();out.append(None)
        else:out.append(getattr(obj,op)(*args))
    return out
