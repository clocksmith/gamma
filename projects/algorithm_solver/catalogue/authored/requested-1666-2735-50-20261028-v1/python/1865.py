"""Original candidate; no qualification or admission."""

from collections import Counter

class FindSumPairs:
    def __init__(self,nums1,nums2):self.first=list(nums1);self.second=list(nums2);self.counts=Counter(nums2)
    def add(self,index,val):
        self.counts[self.second[index]]-=1;self.second[index]+=val;self.counts[self.second[index]]+=1
    def count(self,tot):return sum(self.counts[tot-value] for value in self.first)


def solve(operations, arguments):
    instance = FindSumPairs(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
