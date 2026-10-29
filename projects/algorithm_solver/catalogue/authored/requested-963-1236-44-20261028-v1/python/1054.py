"""Original candidate; no qualification or admission."""

from collections import Counter

def solve(barcodes):
    out=[0]*len(barcodes);position=0
    for value,count in sorted(Counter(barcodes).items(),key=lambda pair:(-pair[1],pair[0])):
        for _ in range(count):
            if position>=len(out):position=1
            out[position]=value;position+=2
    return out


class Solution:
    def rearrangeBarcodes(self, barcodes):
        return solve(barcodes)
