class Solution {
  findMaxAverage(nums, k) {
    let total = 0;
    for (let index = 0; index < k; index += 1) {
      total += nums[index];
    }
    let best = total;
    for (let index = k; index < nums.length; index += 1) {
      total -= nums[index - k];
      total += nums[index];
      best = Math.max(best, total);
    }
    return best / k;
  }
}
