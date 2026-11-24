w,h,c=input().split()
w=int(w)
h=int(h)
a=""
d=""
d_e=""
cnt=2

for i in range(w-2):
    cnt+=1
    a+="-"
    d+="."
    if cnt!=w//2+2:
        d_e+="."
    else:
        d_e+=c
    
print("+"+a+"+")

cnt=2

for j in range(h-2):
    cnt+=1
    if cnt!=h//2+2:
        print("|"+d+"|")
    else :
        print("|"+d_e+"|")
print("+"+a+"+")
        
        

