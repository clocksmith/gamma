class Solution:
    def flipAndInvertImage(self, image: list[list[int]]) -> list[list[int]]:
        for row in image:
            left = 0
            right = len(row) - 1
            while left <= right:
                first = row[left]
                last = row[right]
                row[left] = 1 - last
                row[right] = 1 - first
                left += 1
                right -= 1
        return image
