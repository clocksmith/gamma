function solve(values, other) {
  let index = values.length - 1;
  let index2 = other.length - 1;
  while (index >= 0 || index2 >= 0) {
    index = helper(values, index);
    index2 = helper(other, index2);
    if (index < 0 || index2 < 0) {
      return index === index2;
    }
    if (values.codePointAt(index) !== other.codePointAt(index2)) {
      return false;
    }
    index -= 1;
    index2 -= 1;
  }
  return true;
}
function helper(values2, other2) {
  let count = 0;
  while (other2 >= 0) {
    const value = values2.charCodeAt(other2);
    if (value >= 56320 && value <= 57343 && other2 > 0) {
      const left = values2.charCodeAt(other2 - 1);
      if (left >= 55296 && left <= 56319) {
        other2 -= 1;
      }
    }
    const value2 = values2.codePointAt(other2);
    if (value2 === 35) {
      count += 1;
    } else if (count > 0) {
      count -= 1;
    } else {
      return other2;
    }
    other2 -= 1;
  }
  return -1;
}
