function findMin(nums) {
  let low = 0;
  let high = nums.length - 1;

  while (low < high) {
    const middle = low + Math.floor((high - low) / 2);

    if (nums[middle] > nums[high]) {
      low = middle + 1;
    } else if (nums[middle] < nums[high]) {
      high = middle;
    } else {
      high -= 1;
    }
  }

  return nums[low];
}
