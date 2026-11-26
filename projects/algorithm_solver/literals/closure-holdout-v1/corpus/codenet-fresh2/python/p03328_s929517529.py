a, b = map(int, input().split())

c = b-a

pole = 0

for i in range(c):
  pole += i

print(pole-a)