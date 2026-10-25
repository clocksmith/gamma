def solve(year, month):
    leap = year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)
    days = [0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return days[month]
