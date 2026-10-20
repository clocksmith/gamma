function maxProduct(nums) {
  let maximumEnding = nums[0];
  let minimumEnding = nums[0];
  let best = nums[0];

  for (let index = 1; index < nums.length; index += 1) {
    const value = nums[index];

    if (value < 0) {
      [maximumEnding, minimumEnding] = [minimumEnding, maximumEnding];
    }

    maximumEnding = Math.max(value, maximumEnding * value);
    minimumEnding = Math.min(value, minimumEnding * value);
    best = Math.max(best, maximumEnding);
  }

  return best;
}
