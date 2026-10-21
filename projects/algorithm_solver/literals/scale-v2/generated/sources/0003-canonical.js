function solve(values) {
  const value = new Map();
  let index = 0;
  let index2 = 0;
  let maximum = 0;
  for (const value2 of values) {
    const index3 = value.get(value2);
    if (index3 !== undefined && index3 >= index) {
      index = index3 + 1;
    }
    value.set(value2, index2);
    maximum = Math.max(maximum, index2 - index + 1);
    index2++;
  }
  return maximum;
}
