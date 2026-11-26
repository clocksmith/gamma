tanku=[5,7,5,7,7]
while True:
    n = int(input())
    
    if n == 0:
        break
    
    b = 0
    l = []
    wlen = 0
    for i in range(n):
        w = str(input())
        wlen = len(w)
        l.append(wlen)
        
    for i in range(len(l)):
        a = 0
        tan = 0
        for j in range(i,len(l)):
            a += l[j]
            
            if a > tanku[tan]:
                break
            
            elif a == tanku[tan]:
                if tan != 4:
                    tan += 1
                    a = 0
                elif tan == 4:
                    print(i+1)
                    b += 1
                    break
        if b != 0:
            break
