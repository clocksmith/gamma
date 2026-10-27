# Original candidate implementation. Contract: https://leetcode.com/problems/design-memory-allocator/
class Allocator:
    def __init__(self,n):self.memory=[0]*n
    def allocate(self,size,mID):
        run=0
        for i,value in enumerate(self.memory):
            run=run+1 if value==0 else 0
            if run==size:
                start=i-size+1
                for j in range(start,i+1):self.memory[j]=mID
                return start
        return -1
    def freeMemory(self,mID):
        count=0
        for i,value in enumerate(self.memory):
            if value==mID:self.memory[i]=0;count+=1
        return count

def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='Allocator':obj=Allocator(*args);out.append(None)
        else:out.append(getattr(obj,op)(*args))
    return out
