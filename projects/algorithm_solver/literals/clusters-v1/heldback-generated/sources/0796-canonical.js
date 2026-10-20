function solve(values, other) {
  if (values.length !== other.length) {
    return false;
  }
  if (other.length === 0) {
    return true;
  }
  const size = helper(other);
  let size2 = 0;
  for (let index = 0; index < 2 * values.length - 1; index += 1) {
    const value = values[index % values.length];
    while (size2 > 0 && value !== other[size2]) {
      size2 = size[size2 - 1];
    }
    if (value === other[size2]) {
      size2 += 1;
    }
    if (size2 === other.length) {
      return true;
    }
  }
  return false;
}
function helper(values2) {
  const size3 = new Array(values2.length).fill(0);
  let size4 = 0;
  for (let index2 = 1; index2 < values2.length; index2 += 1) {
    while (size4 > 0 && values2[size4] !== values2[index2]) {
      size4 = size3[size4 - 1];
    }
    if (values2[size4] === values2[index2]) {
      size4 += 1;
    }
    size3[index2] = size4;
  }
  return size3;
}
