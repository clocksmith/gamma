function solve(values) {
  let value = 0;
  for (const value2 of values) {
    value ^= value2;
  }
  return value;
}
