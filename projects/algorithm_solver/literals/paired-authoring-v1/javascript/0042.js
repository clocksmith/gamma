class Solution {
  trap(height) {
    let left = 0;
    let right = height.length - 1;
    let leftMax = 0;
    let rightMax = 0;
    let water = 0;
    while (left <= right) {
      if (leftMax <= rightMax) {
        leftMax = Math.max(leftMax, height[left]);
        water += leftMax - height[left];
        left += 1;
      } else {
        rightMax = Math.max(rightMax, height[right]);
        water += rightMax - height[right];
        right -= 1;
      }
    }
    return water;
  }
}
