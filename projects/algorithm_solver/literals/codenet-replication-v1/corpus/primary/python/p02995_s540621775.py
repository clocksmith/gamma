import sys
from fractions import gcd

input = sys.stdin.readline
A, B, C, D = map(int, input().split(' '))
num = B - A + 1
div_c = B // C - (A - 1) // C
div_d = B // D - (A - 1) // D
lcd = C * D // gcd(C, D)
div_cd = B // lcd - (A - 1) // lcd
print(num - div_c - div_d + div_cd)