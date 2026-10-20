function solve(values, other) {
  const index = lowerBound(values, other);
  if (index < values.length && values[index] === other) {
    return index;
  }
  return -1;
}
function helper(values2, other2) {
  let index2 = 0;
  let index3 = values2.length;
  while (index2 < index3) {
    const index4 = index2 + Math.floor((index3 - index2) / 2);
    if (values2[index4] < other2) {
      index2 = index4 + 1;
    } else {
      index3 = index4;
    }
  }
  return index2;
}
