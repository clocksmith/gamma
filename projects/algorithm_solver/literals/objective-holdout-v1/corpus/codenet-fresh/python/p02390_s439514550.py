S = int(input())
h = S//3600
m = (S-3600*h)//60
s = S-3600*h-60*m
print(str(h)+":"+str(m)+":"+str(s))