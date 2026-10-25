class Solution {
  smallestRangeII(nums, k) {
    const ordered = nums.slice().sort((left, right) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    });
    let best = ordered[ordered.length - 1] - ordered[0];
    for (let index = 0; index < ordered.length - 1; index += 1) {
      const highest = Math.max(ordered[ordered.length - 1] - k, ordered[index] + k);
      const lowest = Math.min(ordered[0] + k, ordered[index + 1] - k);
      best = Math.min(best, highest - lowest);
    }
    return best;
  }
}
