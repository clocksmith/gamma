function solve(values) {
  const count = values.length;
  for (const items of values) {
    let index = 0;
    let index2 = count - 1;
    while (index < index2) {
      if (items[index] === items[index2]) {
        items[index] = toggleLowBit(items[index]);
        items[index2] = toggleLowBit(items[index2]);
      }
      index += 1;
      index2 -= 1;
    }
    if (index === index2) {
      items[index] = toggleLowBit(items[index]);
    }
  }
  return values;
}
function helper(values2) {
  if (values2 % 2 === 0) {
    return values2 + 1;
  }
  return values2 - 1;
}
