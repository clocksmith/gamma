def Z(s,ls):
    lcp = [0]*ls
    lcp[0] = ls
    i,j = 1,0
    while i < ls:
        while i+j < ls and s[j] == s[i+j]:
            j += 1
        lcp[i] = j
        if j == 0:
            i += 1
            continue
        k = 1
        while i+k < ls and k + lcp[k] < j:
            lcp[i+k] = lcp[k]
            k += 1
        i += k
        j -= k
    for i in range(ls):
        lcp[i] = min(lcp[i],i)
    return max(lcp)

n = int(input())
s = list(map(ord,list(input())))
print(max(Z(s[i:],n-i) for i in range(n)))