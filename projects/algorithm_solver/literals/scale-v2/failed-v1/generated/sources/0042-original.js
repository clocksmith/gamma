/* 42. Trapping Rain Water */
function trap(height) {
  let leftIndex = 0;
  let rightIndex = height.length - 1;
  let leftMaximum = 0;
  let rightMaximum = 0;
  let trappedWater = 0;
  while (leftIndex < rightIndex) {
    if (height[leftIndex] <= height[rightIndex]) {
      leftMaximum = Math.max(leftMaximum, height[leftIndex]);
      trappedWater += leftMaximum - height[leftIndex];
      leftIndex++;
    } else {
      rightMaximum = Math.max(rightMaximum, height[rightIndex]);
      trappedWater += rightMaximum - height[rightIndex];
      rightIndex--;
    }
  }
  return trappedWater;
}
