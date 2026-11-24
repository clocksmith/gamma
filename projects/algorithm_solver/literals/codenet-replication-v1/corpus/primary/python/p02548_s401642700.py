N = int(input())

count = 1#よくわからない、1とその数のぶんか？
for i in range(1, N-1):
  count += (N-1)//i
print(count)