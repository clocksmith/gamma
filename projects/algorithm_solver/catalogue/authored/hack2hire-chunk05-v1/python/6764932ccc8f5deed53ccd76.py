"""Original hack2hire:6764932ccc8f5deed53ccd76; inferred public-preview contract; qualification unknown."""
from itertools import permutations

def isValidDate(a, b, c):
    for year, month, day in permutations((a, b, c)):
        if not (1 <= year <= 9999 and 1 <= month <= 12 and day >= 1):
            continue
        leap = year % 400 == 0 or year % 4 == 0 and year % 100 != 0
        lengths = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        if day <= lengths[month - 1]:
            return True
    return False

solve = isValidDate

class Solution:
    isValidDate = staticmethod(isValidDate)
