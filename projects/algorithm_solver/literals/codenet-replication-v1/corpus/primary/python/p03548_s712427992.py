# coding: UTF-8
import math

X, Y, Z = map(int, input().split())
NUM = math.floor((X - Z) / (Y + Z))

print(NUM)