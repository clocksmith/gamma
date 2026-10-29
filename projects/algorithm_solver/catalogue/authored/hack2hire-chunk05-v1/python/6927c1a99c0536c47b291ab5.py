"""Original hack2hire:6927c1a99c0536c47b291ab5; inferred public-preview contract; qualification unknown."""
def distinctPrimeProducts(primes):
    products = {1}
    for prime in primes:
        products.update([value * prime for value in products])
    products.discard(1)
    return sorted(products)

solve = distinctPrimeProducts

class Solution:
    distinctPrimeProducts = staticmethod(distinctPrimeProducts)
