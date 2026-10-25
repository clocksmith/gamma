class Solution:
    def canPlaceFlowers(self, flowerbed: list[int], n: int) -> bool:
        if n == 0:
            return True

        planted = 0
        previous = 0
        for index, current in enumerate(flowerbed):
            following = flowerbed[index + 1] if index + 1 < len(flowerbed) else 0
            if previous == 0 and current == 0 and following == 0:
                planted += 1
                previous = 1
                if planted >= n:
                    return True
            else:
                previous = current
        return False
