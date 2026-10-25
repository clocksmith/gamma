class Solution:
    def stoneGameVI(self, aliceValues: list[int], bobValues: list[int]) -> int:
        order = sorted(range(len(aliceValues)), key=lambda index: (-(aliceValues[index] + bobValues[index]), index))
        difference = 0
        for turn, index in enumerate(order):
            if turn % 2 == 0:
                difference += aliceValues[index]
            else:
                difference -= bobValues[index]
        if difference > 0:
            return 1
        if difference < 0:
            return -1
        return 0
