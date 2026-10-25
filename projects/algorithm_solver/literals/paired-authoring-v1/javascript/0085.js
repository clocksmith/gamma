function histogramArea(heights) {
  const stack = [];
  let best = 0;
  const count = heights.length;
  for (let right = 0; right <= count; right += 1) {
    // A virtual zero flushes the stack without changing heights.
    const current = right < count ? heights[right] : 0;
    let start = right;
    // Entries have increasing starts and strictly increasing positive heights.
    // Each start is the earliest column supporting that height through right - 1.
    while (stack.length > 0 && stack[stack.length - 1][1] > current) {
      const [left, height] = stack.pop();
      best = Math.max(best, height * (right - left));
      start = left;
    }
    // Equal heights retain the earlier start instead of adding duplicates.
    if (current > 0 && (stack.length === 0 || stack[stack.length - 1][1] < current)) {
      stack.push([start, current]);
    }
  }
  return best;
}

class Solution {
  maximalRectangle(matrix) {
    if (matrix.length === 0 || matrix[0].length === 0) {
      return 0;
    }
    const columns = matrix[0].length;
    const heights = Array(columns).fill(0);
    let best = 0;
    for (const row of matrix) {
      for (let column = 0; column < columns; column += 1) {
        if (row[column] === "1") {
          heights[column] += 1;
        } else {
          heights[column] = 0;
        }
      }
      best = Math.max(best, histogramArea(heights));
    }
    return best;
  }
}
