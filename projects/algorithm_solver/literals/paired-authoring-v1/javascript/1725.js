class Solution {
  countGoodRectangles(rectangles) {
    let largest = 0;
    let count = 0;
    for (const [length, width] of rectangles) {
      const side = Math.min(length, width);
      if (side > largest) {
        largest = side;
        count = 1;
      } else if (side === largest) {
        count += 1;
      }
    }
    return count;
  }
}
