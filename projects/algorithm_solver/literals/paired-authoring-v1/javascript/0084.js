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
  largestRectangleArea(heights) {
    return histogramArea(heights);
  }
}
