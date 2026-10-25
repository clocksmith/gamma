class Solution {
  maxAbsValExpr(arr1, arr2) {
    let best = 0;
    for (const firstSign of [-1, 1]) {
      for (const secondSign of [-1, 1]) {
        let lowest = firstSign * arr1[0] + secondSign * arr2[0];
        let highest = lowest;
        for (let index = 1; index < arr1.length; index += 1) {
          const value = firstSign * arr1[index] + secondSign * arr2[index] + index;
          lowest = Math.min(lowest, value);
          highest = Math.max(highest, value);
        }
        best = Math.max(best, highest - lowest);
      }
    }
    return best;
  }
}
