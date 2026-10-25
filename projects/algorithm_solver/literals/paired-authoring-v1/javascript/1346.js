class Solution {
  checkIfExist(arr) {
    const seen = new Set();
    for (const value of arr) {
      if (seen.has(2 * value)) {
        return true;
      }
      if (value % 2 === 0 && seen.has(value / 2)) {
        return true;
      }
      seen.add(value);
    }
    return false;
  }
}
