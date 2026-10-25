class Solution {
  heightChecker(heights) {
    const expected = heights.slice().sort((first, second) => first - second);
    let mismatches = 0;
    for (let index = 0; index < heights.length; index += 1) {
      if (heights[index] !== expected[index]) {
        mismatches += 1;
      }
    }
    return mismatches;
  }
}
