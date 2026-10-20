function solve(values, other) {
  if (other <= 0) {
    return true;
  }
  let count = other;
  let left = 0;
  for (let index = 0; index < values.length; index += 1) {
    const right = index + 1 < values.length ? values[index + 1] : 0;
    if (values[index] === 0 && left === 0 && right === 0) {
      count -= 1;
      left = 1;
      if (count <= 0) {
        return true;
      }
    } else {
      left = values[index];
    }
  }
  return false;
}
