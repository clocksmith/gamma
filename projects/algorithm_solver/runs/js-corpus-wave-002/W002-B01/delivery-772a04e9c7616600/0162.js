function findPeakElement(nums) {
  let low = 0;
  let high = nums.length - 1;

  while (low < high) {
    const middle = low + Math.floor((high - low) / 2);

    if (nums[middle] > nums[middle + 1]) {
      high = middle;
    } else {
      low = middle + 1;
    }
  }

  return low;
}
