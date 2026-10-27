# Original implementation. Contract: https://leetcode.com/problems/find-consecutive-integers-from-a-data-stream/
class DataStream:
    def __init__(self,value,k):self.value=value;self.k=k;self.run=0
    def consec(self,num):self.run=self.run+1 if num==self.value else 0;return self.run>=self.k
def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='DataStream':obj=DataStream(*args);out.append(None)
        else:out.append(obj.consec(*args))
    return out
