function solve(values) {
  const items = helper2(values);
  let count = 0;
  for (let index = 0; index < values.length; index += 1) {
    if (values[index] !== items[index]) {
      count += 1;
    }
  }
  return count;
}
function helper(values2, other, target) {
  while (other * 2 + 1 < target) {
    let index2 = other * 2 + 1;
    if (index2 + 1 < target && values2[index2] < values2[index2 + 1]) {
      index2 += 1;
    }
    if (values2[other] >= values2[index2]) {
      return;
    }
    const value = values2[other];
    values2[other] = values2[index2];
    values2[index2] = value;
    other = index2;
  }
}
function helper2(values3) {
  const items2 = values3.slice();
  for (let index3 = Math.floor(items2.length / 2) - 1; index3 >= 0; index3 -= 1) {
    helper(items2, index3, items2.length);
  }
  for (let size = items2.length - 1; size > 0; size -= 1) {
    const value2 = items2[0];
    items2[0] = items2[size];
    items2[size] = value2;
    helper(items2, 0, size);
  }
  return items2;
}
