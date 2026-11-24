n = int(input())
a = list(map(int,input().split()))
current =0
cost =[]
a.append(0)
for i in range(n):
    cost.append(abs(a[i]-current))
    current=a[i]
cost.append(abs(current))
costTotal = sum(cost)
current =0
for i in range(n):
    print(costTotal-cost[i]-cost[i+1]+abs(a[i+1]-current))
    current=a[i]