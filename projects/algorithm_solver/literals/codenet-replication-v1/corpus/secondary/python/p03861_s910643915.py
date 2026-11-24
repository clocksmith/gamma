from sys import stdin
a, b, x = [int(x) for x in stdin.readline().rstrip().split()]
print((b//x) - (a-1)//x)