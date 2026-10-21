def shortest_clear_matrix_path(grid_values: list[list[int]]) -> int:
    if grid_values[0][0]:
        return (-1)
    grid_size = len(grid_values)
    grid_values[0][0] = 1
    queue_values = [[0, 0]]
    queue_index = 0
    path_length = 1
    while (queue_index < len(queue_values)):
        layer_stop = len(queue_values)
        while (queue_index < layer_stop):
            (row_index, column_index) = queue_values[queue_index]
            queue_index += 1
            if ((row_index == (grid_size - 1)) and (column_index == (grid_size - 1))):
                return path_length
            for next_row in range((row_index - 1), (row_index + 2)):
                for next_column in range((column_index - 1), (column_index + 2)):
                    if ((0 <= next_row < grid_size) and (0 <= next_column < grid_size) and (grid_values[next_row][next_column] == 0)):
                        grid_values[next_row][next_column] = 1
                        queue_values.append([next_row, next_column])
        path_length += 1
    return (-1)

class Solution:
    def shortestPathBinaryMatrix(self, grid: list[list[int]]) -> int:
        return shortest_clear_matrix_path(grid)
