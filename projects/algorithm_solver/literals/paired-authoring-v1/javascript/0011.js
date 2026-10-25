class Solution {
  maxArea(height) {
    let left = 0;
    let right = height.length - 1;
    let best = 0;
    while (left < right) {
      const area = (right - left) * Math.min(height[left], height[right]);
      best = Math.max(best, area);
      // No narrower pair using the shorter endpoint can beat this area.
      // Thus any pair improving best remains inside the next interval.
      if (height[left] <= height[right]) {
        left += 1;
      } else {
        right -= 1;
      }
    }
    return best;
  }
}
