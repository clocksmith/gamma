function solve(values) {
  const items = {};
  for (const value of values) {
    if (items[value]) {
      return value;
    }
    items[value] = true;
  }
  return null;
}
