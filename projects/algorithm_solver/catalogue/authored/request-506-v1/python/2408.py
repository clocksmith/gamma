# Original implementation. Contract: https://leetcode.com/problems/design-sql/
class SQL:
    def __init__(self,names,columns):self.columns=dict(zip(names,columns));self.rows={n:{} for n in names};self.next={n:1 for n in names}
    def ins(self,name,row):
        if name not in self.rows or len(row)!=self.columns[name]:return False
        i=self.next[name];self.next[name]+=1;self.rows[name][i]=row[:];return True
    def rmv(self,name,rowId):
        if name in self.rows:self.rows[name].pop(rowId,None)
    def sel(self,name,rowId,columnId):
        row=self.rows.get(name,{}).get(rowId)
        return row[columnId-1] if row is not None and 1<=columnId<=len(row) else '<null>'
    def exp(self,name):return [','.join([str(i)]+row) for i,row in self.rows.get(name,{}).items()]
def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='SQL':obj=SQL(*args);out.append(None)
        else:out.append(getattr(obj,op)(*args))
    return out
