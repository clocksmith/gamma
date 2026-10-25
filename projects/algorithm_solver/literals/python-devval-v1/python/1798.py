def solve(coins):
    reachable = 1
    for coin in sorted(coins):
        if coin > reachable:
            break
        reachable += coin
    return reachable
