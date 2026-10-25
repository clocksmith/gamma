def solve(house_count, wells, pipes):
    for index, cost in enumerate(wells):
        pipes.append([0, index + 1, cost])
    pipes.sort(key=lambda pipe: pipe[2])
    parents = list(range(house_count + 1))

    def find(house):
        while house != parents[house]:
            parents[house] = parents[parents[house]]
            house = parents[house]
        return house

    total = 0
    remaining = house_count
    for first, second, cost in pipes:
        first, second = find(first), find(second)
        if first != second:
            parents[first] = second
            remaining -= 1
            total += cost
            if remaining == 0:
                return total
    return None
