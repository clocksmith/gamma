function solve(values) {
  const value = {};
  let maximum = 0;
  for (const [value2, value3] of values) {
    if (!value['$' + value2]) {
      value['$' + value2] = [];
    }
    const items = value['$' + value2];
    let index = 0;
    while (index < items.length && items[index] > value3) {
      index += 1;
    }
    items.splice(index, 0, value3);
    if (items.length > 5) {
      items.pop();
    }
    maximum = Math.max(maximum, value2);
  }
  const result = [];
  for (let value4 = 1; value4 <= maximum; value4 += 1) {
    const items2 = value['$' + value4] || [];
    if (items2.length) {
      let total = 0;
      for (const value5 of items2.slice(0, 5)) {
        total += value5;
      }
      result.push([
        value4,
        Math.floor(total / 5)
      ]);
    }
  }
  return result;
}
