while True:
    d, w, h = (int(x) for x in input().split())
    if d == 0: break
    q = int(input())
    vmin = min(d * d + w * w, d * d + h * h, w * w + h * h)
    
    for i in range(0,q):
    	r = int(input())
    	ans = 'NA'
    	if (2 * r) ** 2 > vmin:
    	    ans = 'OK'
    	print(ans)
