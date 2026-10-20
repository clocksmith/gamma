function solve(values, other) {
  const counts = helper2(values);
  let value = null;
  for (const value2 of other) {
    if (value !== null && value2.length >= value.length) {
      continue;
    }
    const counts2 = helper(value2);
    let value3 = true;
    for (let index = 0; index < 26; index += 1) {
      if (counts2[index] < counts[index]) {
        value3 = false;
        break;
      }
    }
    if (value3) {
      value = value2;
    }
  }
  return value;
}
function helper(values2) {
  const counts3 = new Array(26).fill(0);
  for (const value4 of values2) {
    const index2 = value4.charCodeAt(0) - 97;
    counts3[index2] += 1;
  }
  return counts3;
}
function helper2(values3) {
  const counts4 = new Array(26).fill(0);
  for (const value5 of values3) {
    let index3 = value5.charCodeAt(0) - 65;
    if (index3 >= 0 && index3 < 26) {
      counts4[index3] += 1;
    } else {
      index3 = value5.charCodeAt(0) - 97;
      if (index3 >= 0 && index3 < 26) {
        counts4[index3] += 1;
      }
    }
  }
  return counts4;
}
