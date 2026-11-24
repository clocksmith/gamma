num = int(input())
a = input().split()
b = list(map(int, a))
sum = sum(b)

X = [0]*num
X1 = 0
for i in range(num):
  if((2*i+1) >= num):
    break
  X1 = b[2*i+1] + X1
X[0] = sum - 2 * X1

for i in range(1,num):
  X[i] = b[i-1]*2 - X[i-1]
print(" ".join(map(str, X)))