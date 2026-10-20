function solve(values) {
  const items = helper2(values);
  for (let index2 = 0; index2 < values.length; index2 += 1) {
    values[index2] = items[index2];
  }
  let index = values.length;
  while (index > 2) {
    const total = values[index - 2] + values[index - 3];
    if (total > values[index - 1]) {
      return total + values[index - 1];
    }
    index -= 1;
  }
  return 0;
}
function helper(values2, other, target) {
  while (other * 2 + 1 < target) {
    let index3 = other * 2 + 1;
    if (index3 + 1 < target && values2[index3] < values2[index3 + 1]) {
      index3 += 1;
    }
    if (values2[other] >= values2[index3]) {
      return;
    }
    const value = values2[other];
    values2[other] = values2[index3];
    values2[index3] = value;
    other = index3;
  }
}
function helper2(values3) {
  const items2 = values3.slice();
  for (let index4 = Math.floor(items2.length / 2) - 1; index4 >= 0; index4 -= 1) {
    helper(items2, index4, items2.length);
  }
  for (let size = items2.length - 1; size > 0; size -= 1) {
    const value2 = items2[0];
    items2[0] = items2[size];
    items2[size] = value2;
    helper(items2, 0, size);
  }
  return items2;
}
