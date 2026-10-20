function minPatches(nums, n) {
  let missing = 1;
  let index = 0;
  let patches = 0;

  while (missing <= n) {
    if (index < nums.length && nums[index] <= missing) {
      missing += nums[index++];
    } else {
      missing += missing;
      patches++;
    }
  }
  return patches;
}
