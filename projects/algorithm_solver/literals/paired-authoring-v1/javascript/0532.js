class Solution {
  findPairs(nums, k) {
    if (k < 0) {
      return 0;
    }

    const counts = new Map();
    for (const value of nums) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
    let pairs = 0;
    for (const [value, count] of counts) {
      if (k === 0) {
        if (count > 1) {
          pairs += 1;
        }
      } else if (counts.has(value + k)) {
        pairs += 1;
      }
    }
    return pairs;
  }
}
