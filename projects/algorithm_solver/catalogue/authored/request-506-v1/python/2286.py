# Original candidate implementation. Contract: https://leetcode.com/problems/booking-concert-tickets-in-groups/
class BookMyShow:
    def __init__(self,n,m):
        self.n=n;self.m=m;self.free=[m]*n;self.total=[0]*(4*n);self.largest=[0]*(4*n)
        def build(p,l,r):
            self.total[p]=(r-l+1)*m;self.largest[p]=m
            if l<r:
                mid=(l+r)//2;build(p*2,l,mid);build(p*2+1,mid+1,r)
        build(1,0,n-1)
    def update(self,index,value):
        self.free[index]=value
        def put(p,l,r):
            if l==r:self.total[p]=self.largest[p]=value;return
            mid=(l+r)//2
            if index<=mid:put(p*2,l,mid)
            else:put(p*2+1,mid+1,r)
            self.total[p]=self.total[p*2]+self.total[p*2+1];self.largest[p]=max(self.largest[p*2],self.largest[p*2+1])
        put(1,0,self.n-1)
    def first(self,k,limit):
        def find(p,l,r):
            if l>limit or self.largest[p]<k:return -1
            if l==r:return l
            mid=(l+r)//2;left=find(p*2,l,mid)
            return left if left>=0 else find(p*2+1,mid+1,r)
        return find(1,0,self.n-1)
    def prefix(self,limit):
        def total(p,l,r):
            if l>limit:return 0
            if r<=limit:return self.total[p]
            mid=(l+r)//2;return total(p*2,l,mid)+total(p*2+1,mid+1,r)
        return total(1,0,self.n-1)
    def gather(self,k,maxRow):
        row=self.first(k,maxRow)
        if row<0:return []
        seat=self.m-self.free[row];self.update(row,self.free[row]-k);return [row,seat]
    def scatter(self,k,maxRow):
        if self.prefix(maxRow)<k:return False
        while k:
            row=self.first(1,maxRow);take=min(k,self.free[row]);self.update(row,self.free[row]-take);k-=take
        return True

def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='BookMyShow':obj=BookMyShow(*args);out.append(None)
        else:out.append(getattr(obj,op)(*args))
    return out
