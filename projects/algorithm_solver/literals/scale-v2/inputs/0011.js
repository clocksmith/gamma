function maxArea(height) {
  let leftIndex = 0;
  let rightIndex = height.length - 1;
  let maximumArea = 0;
  while (leftIndex < rightIndex) {
    const area = Math.min(height[leftIndex], height[rightIndex]) * (rightIndex - leftIndex);
    maximumArea = Math.max(maximumArea, area);
    if (height[leftIndex] <= height[rightIndex]) {
      leftIndex++;
    } else {
      rightIndex--;
    }
  }
  return maximumArea;
}
