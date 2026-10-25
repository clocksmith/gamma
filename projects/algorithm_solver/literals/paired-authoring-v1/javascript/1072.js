class Solution {
  maxEqualRowsAfterFlips(matrix) {
    const frequencies = new Map();
    let best = 0;
    for (const row of matrix) {
      const pattern = [];
      for (const value of row) {
        pattern.push(value === row[0] ? "0" : "1");
      }
      const key = pattern.join("");
      const count = (frequencies.get(key) ?? 0) + 1;
      frequencies.set(key, count);
      best = Math.max(best, count);
    }
    return best;
  }
}
