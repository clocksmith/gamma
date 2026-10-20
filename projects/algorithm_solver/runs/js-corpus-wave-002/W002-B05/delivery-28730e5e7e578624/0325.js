function maxSubArrayLen(nums, k) {
  const earliest = new Map([[0, -1]]);
  let total = 0;
  let best = 0;

  for (let index = 0; index < nums.length; index++) {
    total += nums[index];
    if (earliest.has(total - k)) {
      best = Math.max(best, index - earliest.get(total - k));
    }
    if (!earliest.has(total)) earliest.set(total, index);
  }
  return best;
}
