class Solution {
  maximumNumberOfOnes(width, height, sideLength, maxOnes) {
    const weights = [];
    for (let row = 0; row < sideLength; row += 1) {
      const rowCount = Math.floor((height + sideLength - 1 - row) / sideLength);
      for (let column = 0; column < sideLength; column += 1) {
        const columnCount = Math.floor((width + sideLength - 1 - column) / sideLength);
        weights.push(rowCount * columnCount);
      }
    }
    weights.sort((left, right) => right - left);
    let total = 0;
    for (let index = 0; index < maxOnes; index += 1) {
      total += weights[index];
    }
    return total;
  }
}
