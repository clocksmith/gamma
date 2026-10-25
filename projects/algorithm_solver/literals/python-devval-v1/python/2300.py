from bisect import bisect_left


def solve(spells, potions, success):
    ordered = sorted(potions)
    result = []
    for spell in spells:
        threshold = (success + spell - 1) // spell
        result.append(len(ordered) - bisect_left(ordered, threshold))
    return result
