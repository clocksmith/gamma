# Original candidate implementation. Contract: https://leetcode.com/problems/design-an-atm-machine/
class ATM:
    def __init__(self):self.counts=[0]*5
    def deposit(self,banknotesCount):
        for i,c in enumerate(banknotesCount):self.counts[i]+=c
    def withdraw(self,amount):
        values=[20,50,100,200,500];used=[0]*5
        for i in range(4,-1,-1):used[i]=min(self.counts[i],amount//values[i]);amount-=used[i]*values[i]
        if amount:return [-1]
        for i in range(5):self.counts[i]-=used[i]
        return used

def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='ATM':obj=ATM();out.append(None)
        else:out.append(getattr(obj,op)(*args))
    return out
