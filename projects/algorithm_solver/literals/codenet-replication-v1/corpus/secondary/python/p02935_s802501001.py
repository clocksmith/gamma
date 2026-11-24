n=int(input())
lst=map(int, input().split())

lst=sorted(lst, reverse=True)
new=[lst[i]*(1/2)**(i+1) for i in range(n-1)]
print(sum(new)+lst[-1]*(1/2)**(n-1))
