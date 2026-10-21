/* 55. Jump Game */
function canJump(nums) {
  let furthestIndex = 0;
  for (let index = 0; index < nums.length; index++) {
    if (index > furthestIndex) {
      return false;
    }
    furthestIndex = Math.max(furthestIndex, index + nums[index]);
  }
  return true;
}
