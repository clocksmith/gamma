function solve(values, other, target) {
  if (values.length !== other.length) {
    return false;
  }
  const key = helper2(target);
  for (let index = 0; index < values.length; index += 1) {
    if (values[index] !== other[index]) {
      const left = helper(values[index]);
      const right = helper(other[index]);
      if (!(left in key) || !(right in key[left])) {
        return false;
      }
    }
  }
  return true;
}
function helper(values2) {
  return '$' + values2;
}
function helper2(values3) {
  const key2 = {};
  for (const value of values3) {
    const left2 = helper(value[0]);
    const right2 = helper(value[1]);
    if (!(left2 in key2)) {
      key2[left2] = {};
    }
    if (!(right2 in key2)) {
      key2[right2] = {};
    }
    key2[left2][right2] = true;
    key2[right2][left2] = true;
  }
  return key2;
}
