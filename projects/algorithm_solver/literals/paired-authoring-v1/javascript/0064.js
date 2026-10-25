class Solution {
  minPathSum(grid) {
    const rows = grid.length;
    const columns = grid[0].length;
    const pathCosts = new Array(columns).fill(0);
    pathCosts[0] = grid[0][0];
    for (let column = 1; column < columns; column += 1) {
      pathCosts[column] = pathCosts[column - 1] + grid[0][column];
    }
    for (let row = 1; row < rows; row += 1) {
      pathCosts[0] += grid[row][0];
      for (let column = 1; column < columns; column += 1) {
        // Read the previous row above and the updated current row left.
        pathCosts[column] = Math.min(
          pathCosts[column], pathCosts[column - 1]
        ) + grid[row][column];
      }
    }
    return pathCosts[columns - 1];
  }
}
