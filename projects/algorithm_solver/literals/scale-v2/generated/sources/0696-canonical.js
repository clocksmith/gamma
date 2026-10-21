function solve(values) {
  let left = 0;
  let size = 0;
  let left2 = '';
  let count = 0;
  for (const value of values) {
    if (value === left2) {
      size += 1;
    } else {
      left = size;
      size = 1;
      left2 = value;
    }
    if (size <= left) {
      count += 1;
    }
  }
  return count;
}
