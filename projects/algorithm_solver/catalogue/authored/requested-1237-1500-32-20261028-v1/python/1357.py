"""Original frontend 1357 variant; qualification unknown."""


class Cashier:
    def __init__(self, n: int, discount: int, products, prices):
        self.n = n
        self.discount = discount
        self.price_map = {p: pr for p, pr in zip(products, prices)}
        self.count = 0

    def getBill(self, product, amount) -> float:
        self.count += 1
        total = sum(self.price_map[p] * a for p, a in zip(product, amount))
        if self.count % self.n == 0:
            return total * (100 - self.discount) / 100.0
        return float(total)


def solve(operation_names, argument_lists):
    n, d, prods, prices = argument_lists[0]
    inst = Cashier(n, d, prods, prices)
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        out.append(inst.getBill(args[0], args[1]))
    return out
