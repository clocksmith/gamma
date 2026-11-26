import datetime
for i in range(3):
    h1,m1,s1,h2,m2,s2=map(int,input().split())
    t_c=datetime.datetime(2019,3,7,h1,m1,s1)
    t_b=datetime.datetime(2019,3,7,h2,m2,s2)
    t_a=str(t_b-t_c)
    ha,hb,hc=map(int,t_a.split(":"))
    print(ha,hb,hc)
