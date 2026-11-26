import sys
t='X'
for e in sys.stdin:
 for i in'0123456789'[(e[0]==t and'+'!=e[1]) or('+X='not in e and'+X'in e )or(e[-1]==t and'=X'in e):]:
  l,r=e.replace(t,i).split('=')
  if sum(map(int,l.split('+')))==int(r):print(i);break
 else:print('NA')
