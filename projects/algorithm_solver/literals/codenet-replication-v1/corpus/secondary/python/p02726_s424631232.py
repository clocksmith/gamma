import sys
def input(): return sys.stdin.readline().rstrip()
def main():
    n,x,y=map(int,input().split())
    x-=1
    y-=1
    ans=[0]*n
    for i in range(n-1):
        for j in range(i+1,n):
            ans[min(j-i,abs(x-i)+1+abs(y-j),abs(x-j)+1+abs(y-i))]+=1
    for a in ans[1:]:
        print(a)


if __name__=='__main__':
    main()