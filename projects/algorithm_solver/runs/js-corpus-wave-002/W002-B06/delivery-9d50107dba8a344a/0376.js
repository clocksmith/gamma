function wiggleMaxLength(nums) {
  if (nums.length === 0) return 0;
  let rising = 1;
  let falling = 1;

  for (let index = 1; index < nums.length; index++) {
    if (nums[index] > nums[index - 1]) rising = falling + 1;
    else if (nums[index] < nums[index - 1]) falling = rising + 1;
  }
  return Math.max(rising, falling);
}
