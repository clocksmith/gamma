while True:
    d= float(input())
    if d< 0: break
    a= bin(int(d))[2:]
    if len(a)> 8:
        print("NA")
    else:
        a= a.zfill(8)+"."
        b= d-int(d)
        for _ in range(4):
            b*= 2
            if int(b)>= 1:
                a= a+'1'
                b-= 1
            else:
                a= a+'0'
        a= a.ljust(13, '0')
        print("NA" if 1e-10 < b or len(a)> 13 else a)