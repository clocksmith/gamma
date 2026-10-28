"""1268. Search Suggestions System (Medium).

Specification: https://leetcode.com/problems/search-suggestions-system/description/
"""


def solve(products: list[str], searchWord: str) -> list[list[str]]:
    ordered = sorted(products)
    result = []
    for length in range(1, len(searchWord) + 1):
        prefix = searchWord[:length]
        matches = []
        for product in ordered:
            if product.startswith(prefix):
                matches.append(product)
                if len(matches) == 3:
                    break
        result.append(matches)
    return result


class Solution:
    def suggestedProducts(self, products: list[str], searchWord: str) -> list[list[str]]:
        return solve(products, searchWord)
