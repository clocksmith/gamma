function solve(values, other) {
  let index = values.length - 1, index2 = other.length - 1, value = 0, result = '';
  while (index >= 0 || index2 >= 0 || value) {
    const total = value + (index >= 0 ? Number(values[index--]) : 0) + (index2 >= 0 ? Number(other[index2--]) : 0);
    result = String(total % 2) + result;
    value = Math.floor(total / 2);
  }
  return result;
}
