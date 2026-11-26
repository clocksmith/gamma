cnt=0
def merge(a,left,mid,right):
    n1=mid-left
    n2=right-mid
    l=a[left:mid]
    r=a[mid:right]
    l.append(float("inf"))
    r.append(float("inf"))
    i=0
    j=0
    for k in range(left,right):
        global cnt
        cnt+=1
        if(l[i] <= r[j]):
            a[k] = l[i]
            i+=1
        else:
            a[k]=r[j]
            j+=1
 
def merge_sort(a,left,right):
    if(left+1<right):
        mid=(left+right)//2
        merge_sort(a,left,mid)
        merge_sort(a,mid,right)
        merge(a,left,mid,right)
 
 
 
n=int(input())
s=input()
a=list(map(int,s.split()))
merge_sort(a,0,n)
a=map(str,a)
print(" ".join(list(a)))
print(cnt)
    
