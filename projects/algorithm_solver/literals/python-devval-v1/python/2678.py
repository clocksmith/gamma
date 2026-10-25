def solve(details):
    return sum(int(detail[11:13]) > 60 for detail in details)
