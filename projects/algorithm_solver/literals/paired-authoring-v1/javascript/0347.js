class Solution {
  topKFrequent(nums, k) {
    const counts = new Map();
    for (const value of nums) {
      counts.set(value, (counts.get(value) ?? 0) + 1);
    }

    const buckets = Array.from({ length: nums.length + 1 }, () => []);
    for (const [value, frequency] of counts) {
      buckets[frequency].push(value);
    }

    const result = [];
    for (let frequency = nums.length; frequency > 0; frequency--) {
      for (const value of buckets[frequency]) {
        result.push(value);
        if (result.length === k) {
          return result;
        }
      }
    }
    return result;
  }
}
