/* 35. Search Insert Position */
function searchInsert(nums, target) {
  let low = 0;
  let high = nums.length;
  while (low < high) {
    const midpoint = low + Math.floor((high - low) / 2);
    if (nums[midpoint] < target) {
      low = midpoint + 1;
    } else {
      high = midpoint;
    }
  }
  return low;
}
