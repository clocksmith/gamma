class Solution {
  triangleNumber(nums) {
    const ordered = nums.slice().sort((left, right) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    });
    let count = 0;
    for (let largest = ordered.length - 1; largest > 1; largest -= 1) {
      let left = 0;
      let right = largest - 1;
      while (left < right) {
        if (ordered[left] + ordered[right] > ordered[largest]) {
          count += right - left;
          right -= 1;
        } else {
          left += 1;
        }
      }
    }
    return count;
  }
}
