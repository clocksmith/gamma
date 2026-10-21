function solve(values) {
  const count = values.length;
  const total = count * (count + 1) / 2;
  let total2 = 0;
  let total3 = 0;
  const items = {};
  for (const value of values) {
    total2 += value;
    if (!items[value]) {
      items[value] = true;
      total3 += value;
    }
  }
  return [
    total2 - total3,
    total - total3
  ];
}
