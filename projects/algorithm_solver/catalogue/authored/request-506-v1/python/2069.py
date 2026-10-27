# Original candidate. Contract: https://leetcode.com/problems/walking-robot-simulation-ii/
def solve(operations, arguments):
    out=[];pos=0;moved=False;w=h=0
    for op,a in zip(operations,arguments):
        if op=='Robot':w,h=a;pos=0;moved=False;out.append(None)
        elif op=='step':pos=(pos+a[0])%(2*(w+h-2));moved=True;out.append(None)
        else:
            if pos==0:x,y,d=0,0,'South' if moved else 'East'
            elif pos<=w-1:x,y,d=pos,0,'East'
            elif pos<=w+h-2:x,y,d=w-1,pos-w+1,'North'
            elif pos<=2*w+h-3:x,y,d=2*w+h-3-pos,h-1,'West'
            else:x,y,d=0,2*(w+h-2)-pos,'South'
            if op=='getPos':out.append([x,y])
            elif op=='getDir':out.append(d)
            else:raise ValueError('unknown operation')
    return out
