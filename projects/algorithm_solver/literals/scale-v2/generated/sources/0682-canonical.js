function solve(values) {
  const items = [];
  for (const value of values) {
    if (value === '+') {
      items.push(items[items.length - 1] + items[items.length - 2]);
    } else if (value === 'D') {
      items.push(items[items.length - 1] * 2);
    } else if (value === 'C') {
      items.pop();
    } else {
      items.push(+value);
    }
  }
  let total = 0;
  for (const value2 of items) {
    total += value2;
  }
  return total;
}
