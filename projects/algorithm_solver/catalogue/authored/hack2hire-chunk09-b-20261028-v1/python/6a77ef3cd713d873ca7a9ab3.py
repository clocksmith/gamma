"""Hack2Hire 6a77ef3cd713d873ca7a9ab3 (Count Incorrect Sale Prices) over an INFERRED spec; qualification unknown."""


def solve(products, productPrices, productSold, soldPrice):
    correct = dict(zip(products, productPrices))
    wrong = 0
    for name, entered in zip(productSold, soldPrice):
        if correct[name] != entered:
            wrong += 1
    return wrong


class Solution:
    def countIncorrect(self, products, productPrices, productSold, soldPrice):
        return solve(products, productPrices, productSold, soldPrice)
