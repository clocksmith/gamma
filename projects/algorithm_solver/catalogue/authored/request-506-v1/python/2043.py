# Original candidate. Contract: https://leetcode.com/problems/simple-bank-system/
def solve(operations, arguments):
    balance=[];out=[]
    for op,a in zip(operations,arguments):
        if op=='Bank':balance=list(a[0]);out.append(None);continue
        valid=lambda x:1<=x<=len(balance)
        if op=='deposit':
            account,money=a;ok=valid(account)
            if ok:balance[account-1]+=money
        elif op=='withdraw':
            account,money=a;ok=valid(account) and balance[account-1]>=money
            if ok:balance[account-1]-=money
        elif op=='transfer':
            x,y,money=a;ok=valid(x) and valid(y) and balance[x-1]>=money
            if ok:balance[x-1]-=money;balance[y-1]+=money
        else:raise ValueError('unknown operation')
        out.append(ok)
    return out
