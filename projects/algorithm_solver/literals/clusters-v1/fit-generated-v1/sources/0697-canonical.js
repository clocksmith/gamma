function solve(values) {
  if (values.length === 0) {
    return 0;
  }
  let minimum = values[0];
  let maximum = values[0];
  for (const value2 of values) {
    if (value2 < minimum) {
      minimum = value2;
    }
    if (value2 > maximum) {
      maximum = value2;
    }
  }
  const counts = new Array(maximum - minimum + 1).fill(0);
  const value = new Array(counts.length).fill(-1);
  let count = 0;
  let size = values.length;
  for (let index = 0; index < values.length; index += 1) {
    const value3 = values[index] - minimum;
    if (value[value3] === -1) {
      value[value3] = index;
    }
    counts[value3] += 1;
    const size2 = index - value[value3] + 1;
    if (counts[value3] > count) {
      count = counts[value3];
      size = size2;
    } else if (counts[value3] === count && size2 < size) {
      size = size2;
    }
  }
  return size;
}
