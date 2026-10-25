class Solution {
  minDeletionSize(strs) {
    const resolved = new Array(strs.length - 1).fill(false);
    let deleted = 0;
    for (let column = 0; column < strs[0].length; column += 1) {
      let invalid = false;
      for (let row = 0; row < strs.length - 1; row += 1) {
        if (!resolved[row] && strs[row][column] > strs[row + 1][column]) {
          invalid = true;
          break;
        }
      }
      if (invalid) {
        deleted += 1;
        continue;
      }
      for (let row = 0; row < strs.length - 1; row += 1) {
        if (strs[row][column] < strs[row + 1][column]) resolved[row] = true;
      }
    }
    return deleted;
  }
}
