from bisect import bisect_right


def solve(rains):
    dry_days = [day for day, lake in enumerate(rains) if lake == 0]
    successor = list(range(len(dry_days) + 1))

    def available(index):
        root = index
        while successor[root] != root:
            root = successor[root]
        while successor[index] != index:
            following = successor[index]
            successor[index] = root
            index = following
        return root

    last_rain = {}
    result = [1 if lake == 0 else -1 for lake in rains]
    for day, lake in enumerate(rains):
        if lake == 0:
            continue
        if lake in last_rain:
            position = available(bisect_right(dry_days, last_rain[lake]))
            if position == len(dry_days) or dry_days[position] > day:
                return []
            result[dry_days[position]] = lake
            successor[position] = position + 1
        last_rain[lake] = day
    return result
