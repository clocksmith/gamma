class Solution {
  distinctDifferenceArray(nums) {
    const remaining = new Map();
    for (const value of nums) {
      remaining.set(value, (remaining.get(value) || 0) + 1);
    }
    const prefix = new Set();
    const output = [];
    for (const value of nums) {
      const count = remaining.get(value) - 1;
      if (count === 0) {
        remaining.delete(value);
      } else {
        remaining.set(value, count);
      }
      prefix.add(value);
      output.push(prefix.size - remaining.size);
    }
    return output;
  }
}
