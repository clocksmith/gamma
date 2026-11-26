a=1/3
while 1:
    z=int(input())
    if z==0:break
    m,zz=0,z*z*z
    for x in range(1,int(z/pow(2,a))+1):
        xx=x*x*x
        y=int(pow(zz-xx,a))
        yy=y*y*y
        m=max(m,yy+xx)
    print(zz-m)