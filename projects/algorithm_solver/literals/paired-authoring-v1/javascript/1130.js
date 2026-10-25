class Solution {
  mctFromLeafValues(arr) {
    const stack = [];
    let cost = 0;
    for (const value of arr) {
      while (stack.length > 0 && stack[stack.length - 1] <= value) {
        const middle = stack.pop();
        const neighbor = stack.length > 0 ? Math.min(stack[stack.length - 1], value) : value;
        cost += middle * neighbor;
      }
      stack.push(value);
    }
    while (stack.length > 1) {
      const middle = stack.pop();
      cost += middle * stack[stack.length - 1];
    }
    return cost;
  }
}
