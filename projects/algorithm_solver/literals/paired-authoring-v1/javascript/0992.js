class Solution {
  subarraysWithKDistinct(nums, k) {
    function atMost(limit) {
      if (limit < 0) return 0;
      const counts = new Map();
      let left = 0;
      let total = 0;
      for (let right = 0; right < nums.length; right += 1) {
        const value = nums[right];
        counts.set(value, (counts.get(value) ?? 0) + 1);
        while (counts.size > limit) {
          const leaving = nums[left];
          const remaining = counts.get(leaving) - 1;
          if (remaining === 0) counts.delete(leaving);
          else counts.set(leaving, remaining);
          left += 1;
        }
        total += right - left + 1;
      }
      return total;
    }

    return atMost(k) - atMost(k - 1);
  }
}
