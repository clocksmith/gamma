function siftDown(heapValues, rootIndex, heapSize) {
  while (rootIndex * 2 + 1 < heapSize) {
    let childIndex = rootIndex * 2 + 1;
    if (childIndex + 1 < heapSize && heapValues[childIndex] < heapValues[childIndex + 1]) {
      childIndex += 1;
    }
    if (heapValues[rootIndex] >= heapValues[childIndex]) {
      return;
    }
    const swapValue = heapValues[rootIndex];
    heapValues[rootIndex] = heapValues[childIndex];
    heapValues[childIndex] = swapValue;
    rootIndex = childIndex;
  }
}
function sortValues(values) {
  const sortedValues = values.slice();
  for (let rootIndex = Math.floor(sortedValues.length / 2) - 1; rootIndex >= 0; rootIndex -= 1) {
    siftDown(sortedValues, rootIndex, sortedValues.length);
  }
  for (let heapSize = sortedValues.length - 1; heapSize > 0; heapSize -= 1) {
    const swapValue = sortedValues[0];
    sortedValues[0] = sortedValues[heapSize];
    sortedValues[heapSize] = swapValue;
    siftDown(sortedValues, 0, heapSize);
  }
  return sortedValues;
}
function largestTrianglePerimeter(values) {
  const sortedValues = sortValues(values);
  for (let valueIndex = 0; valueIndex < values.length; valueIndex += 1) {
    values[valueIndex] = sortedValues[valueIndex];
  }
  let rightBound = values.length;
  while (rightBound > 2) {
    const sideSum = values[rightBound - 2] + values[rightBound - 3];
    if (sideSum > values[rightBound - 1]) {
      return sideSum + values[rightBound - 1];
    }
    rightBound -= 1;
  }
  return 0;
}
function solve(nums) {
  return largestTrianglePerimeter(nums);
}
