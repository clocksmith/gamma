function findMissingRanges(nums, lower, upper) {
  const result = [];
  let previous = lower - 1;

  for (let index = 0; index <= nums.length; index += 1) {
    const current = index < nums.length ? nums[index] : upper + 1;

    if (current - previous >= 2) {
      result.push([previous + 1, current - 1]);
    }

    previous = current;
  }

  return result;
}
