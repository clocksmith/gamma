class Solution {
  maxResult(nums, k) {
    const queue = [[0, nums[0]]];
    let head = 0;
    let score = nums[0];
    for (let index = 1; index < nums.length; index += 1) {
      while (queue[head][0] < index - k) {
        head += 1;
      }
      score = queue[head][1] + nums[index];
      while (queue.length > head && queue[queue.length - 1][1] <= score) {
        queue.pop();
      }
      queue.push([index, score]);
    }
    return score;
  }
}
