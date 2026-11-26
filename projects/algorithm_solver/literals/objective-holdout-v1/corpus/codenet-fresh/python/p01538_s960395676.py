import sys
# -*- coding: utf-8 -*-

def multiple(target,count):
    length = len(target)
    result = []
    if length == 1:
        return count
    for i in range(1,length):
        prefix = int(target[:i])
        suffix = int(target[i:])
        result.append(prefix*suffix)
    return multiple(str(max(result)), count+1)

count=int(input())
for i in range(count):
    print(multiple(input(),0))

