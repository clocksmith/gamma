class Solution {
  floodFill(image, sr, sc, color) {
    const rows = image.length;
    const columns = image[0].length;
    const old_color = image[sr][sc];
    if (old_color === color) {
      return image;
    }

    const queue = [[sr, sc]];
    let head = 0;
    const directions = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    image[sr][sc] = color;
    while (head < queue.length) {
      const [row, column] = queue[head];
      head += 1;
      for (const [row_step, column_step] of directions) {
        const next_row = row + row_step;
        const next_column = column + column_step;
        if (
          next_row < 0
          || next_row >= rows
          || next_column < 0
          || next_column >= columns
        ) {
          continue;
        }
        if (image[next_row][next_column] !== old_color) {
          continue;
        }
        image[next_row][next_column] = color;
        queue.push([next_row, next_column]);
      }
    }
    return image;
  }
}
