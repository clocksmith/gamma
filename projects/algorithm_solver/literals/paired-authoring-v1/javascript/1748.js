class Solution {
  sumOfUnique(nums) {
    const counts = new Map();
    for (const value of nums) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
    let total = 0;
    for (const [value, count] of counts) {
      if (count === 1) {
        total += value;
      }
    }
    return total;
  }
}
