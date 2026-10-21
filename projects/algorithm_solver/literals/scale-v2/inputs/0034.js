/* 34. Find First and Last Position in Sorted Array */
function searchRange(nums, target) {
  function bound(upper) {
    let low = 0;
    let high = nums.length;
    while (low < high) {
      const midpoint = low + Math.floor((high - low) / 2);
      if (nums[midpoint] < target || upper && nums[midpoint] === target) {
        low = midpoint + 1;
      } else {
        high = midpoint;
      }
    }
    return low;
  }
  const leftIndex = bound(false);
  if (leftIndex === nums.length || nums[leftIndex] !== target) {
    return [-1, -1];
  }
  return [leftIndex, bound(true) - 1];
}
