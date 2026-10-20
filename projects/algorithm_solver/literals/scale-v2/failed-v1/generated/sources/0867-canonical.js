function solve(values) {
  if (values.length === 0) {
    return [];
  }
  let count = values[0].length;
  for (const items of values) {
    count = Math.min(count, items.length);
  }
  const result = [];
  for (let index = 0; index < count; index += 1) {
    const items2 = [];
    for (const items3 of values) {
      items2.push(items3[index]);
    }
    result.push(items2);
  }
  return result;
}
