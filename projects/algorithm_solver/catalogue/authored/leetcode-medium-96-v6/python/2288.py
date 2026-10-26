"""2288. Apply Discount to Prices: recognize whole price tokens and format the discount using integer cents."""


def solve(sentence: str, discount: int) -> str:
    """O(L) time and O(L) auxiliary and result space on the bounded price domain; inputs are read-only."""
    tokens = sentence.split(' ')
    for index, token in enumerate(tokens):
        if len(token) > 1 and token[0] == '$' and all('0' <= digit <= '9' for digit in token[1:]):
            cents = int(token[1:]) * (100 - discount)
            tokens[index] = f'${cents // 100}.{cents % 100:02d}'
    return ' '.join(tokens)


class Solution:
    def discountPrices(self, sentence: str, discount: int) -> str:
        return solve(sentence, discount)
