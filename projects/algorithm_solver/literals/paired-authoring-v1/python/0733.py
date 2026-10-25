class Solution:
    def floodFill(
        self, image: list[list[int]], sr: int, sc: int, color: int
    ) -> list[list[int]]:
        rows = len(image)
        columns = len(image[0])
        old_color = image[sr][sc]
        if old_color == color:
            return image

        queue = [(sr, sc)]
        head = 0
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
        image[sr][sc] = color
        while head < len(queue):
            row, column = queue[head]
            head += 1
            for row_step, column_step in directions:
                next_row = row + row_step
                next_column = column + column_step
                if (
                    next_row < 0
                    or next_row >= rows
                    or next_column < 0
                    or next_column >= columns
                ):
                    continue
                if image[next_row][next_column] != old_color:
                    continue
                image[next_row][next_column] = color
                queue.append((next_row, next_column))
        return image
