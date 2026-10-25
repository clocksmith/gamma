class Solution {
  uniquePaths(m, n) {
    const pathCounts = new Array(n).fill(1);
    for (let row = 1; row < m; row += 1) {
      for (let column = 1; column < n; column += 1) {
        // Read the previous row above and the updated current row left.
        pathCounts[column] += pathCounts[column - 1];
      }
    }
    return pathCounts[n - 1];
  }
}
