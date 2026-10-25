class Solution {
  deleteAndEarn(nums) {
    const points = new Map();
    for (const value of nums) {
      points.set(value, (points.get(value) || 0) + value);
    }
    const ordered = Array.from(points.keys()).sort((left, right) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    });
    let take = 0;
    let skip = 0;
    let previous = null;
    for (const value of ordered) {
      const best = Math.max(take, skip);
      if (previous !== null && value === previous + 1) {
        take = skip + points.get(value);
      } else {
        take = best + points.get(value);
      }
      skip = best;
      previous = value;
    }
    return Math.max(take, skip);
  }
}
