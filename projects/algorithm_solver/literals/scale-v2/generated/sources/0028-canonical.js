function solve(values, other) {
  if (other.length === 0) {
    return 0;
  }
  const value = new Array(other.length).fill(0);
  for (let index = 1, size = 0; index < other.length; index++) {
    while (size > 0 && other[index] !== other[size]) {
      size = value[size - 1];
    }
    if (other[index] === other[size]) {
      size++;
    }
    value[index] = size;
  }
  for (let index2 = 0, size2 = 0; index2 < values.length; index2++) {
    while (size2 > 0 && values[index2] !== other[size2]) {
      size2 = value[size2 - 1];
    }
    if (values[index2] === other[size2]) {
      size2++;
    }
    if (size2 === other.length) {
      return index2 - size2 + 1;
    }
  }
  return -1;
}
