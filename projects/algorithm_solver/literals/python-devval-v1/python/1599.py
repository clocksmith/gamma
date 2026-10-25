def solve(customers, boarding_cost, running_cost):
    waiting = 0
    profit = 0
    best_profit = 0
    best_rotation = -1
    rotation = 0
    while rotation < len(customers) or waiting:
        if rotation < len(customers):
            waiting += customers[rotation]
        boarded = min(4, waiting)
        waiting -= boarded
        rotation += 1
        profit += boarded * boarding_cost - running_cost
        if profit > best_profit:
            best_profit = profit
            best_rotation = rotation
    return best_rotation
