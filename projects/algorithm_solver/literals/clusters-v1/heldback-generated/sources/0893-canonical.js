function solve(values) {
  const value = {};
  let count = 0;
  for (const value2 of values) {
    const items = [];
    const items2 = [];
    let index = 0;
    for (const value4 of value2) {
      if (index % 2 === 0) {
        items.push(value4);
      } else {
        items2.push(value4);
      }
      index += 1;
    }
    items.sort(helper2);
    items2.sort(helper2);
    const value3 = helper(items.join('') + items2.join(''));
    if (value[value3] !== true) {
      value[value3] = true;
      count += 1;
    }
  }
  return count;
}
function helper(values2) {
  return '$' + values2;
}
function helper2(values3, other) {
  return values3.codePointAt(0) - other.codePointAt(0);
}
