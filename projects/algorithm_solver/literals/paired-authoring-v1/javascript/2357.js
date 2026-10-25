class Solution {
  minimumOperations(nums) {
    const positive = new Set();
    for (const value of nums) {
      if (value > 0) {
        positive.add(value);
      }
    }
    return positive.size;
  }
}
