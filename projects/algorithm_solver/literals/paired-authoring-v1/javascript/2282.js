function visibleAhead(heights) {
  const output = Array(heights.length).fill(0);
  const stack = [];
  for (let index = heights.length - 1; index >= 0; index -= 1) {
    const height = heights[index];
    while (stack.length > 0 && stack[stack.length - 1] < height) {
      stack.pop();
      output[index] += 1;
    }
    if (stack.length > 0) {
      output[index] += 1;
      if (stack[stack.length - 1] === height) {
        stack.pop();
      }
    }
    stack.push(height);
  }
  return output;
}


class Solution {
  seePeople(heights) {
    const rows = heights.length;
    const columns = rows > 0 ? heights[0].length : 0;
    const output = heights.map(row => visibleAhead(row));
    for (let column = 0; column < columns; column += 1) {
      const columnHeights = Array.from({length: rows}, (_, row) => heights[row][column]);
      const counts = visibleAhead(columnHeights);
      for (let row = 0; row < rows; row += 1) {
        output[row][column] += counts[row];
      }
    }
    return output;
  }
}
