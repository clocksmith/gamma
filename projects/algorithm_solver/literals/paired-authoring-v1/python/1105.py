class Solution:
    def minHeightShelves(self, books: list[list[int]], shelfWidth: int) -> int:
        best = [0] * (len(books) + 1)
        for end in range(1, len(books) + 1):
            best[end] = best[end - 1] + books[end - 1][1]
            width = 0
            height = 0
            for start in range(end - 1, -1, -1):
                width += books[start][0]
                if width > shelfWidth:
                    break
                height = max(height, books[start][1])
                best[end] = min(best[end], best[start] + height)
        return best[-1]
