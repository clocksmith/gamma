import bisect
import sys
input = sys.stdin.readline
N = int(input())
list = list(map(int, input().split()))
list.sort()

score = 0

for i in range (N-2):
    for j in range (i+1, N-1):
        index = bisect.bisect_left(list, list[i] + list[j]) - j - 1
        score += index

print (score)
