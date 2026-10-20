function minCost(costs) {
  let red = 0, blue = 0, green = 0;
  for (const [r, b, g] of costs) {
    [red, blue, green] = [r + Math.min(blue, green), b + Math.min(red, green), g + Math.min(red, blue)];
  }
  return Math.min(red, blue, green);
}
