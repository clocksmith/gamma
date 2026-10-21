function arrangeParity(values) {
  let oddIndex = 1;
  for (let evenIndex = 0; evenIndex < values.length; evenIndex += 2) {
    if (values[evenIndex] % 2 !== 0) {
      while (oddIndex < values.length && values[oddIndex] % 2 !== 0) {
        oddIndex += 2;
      }
      if (oddIndex >= values.length) {
        throw "parity count mismatch";
      }
      const value = values[evenIndex];
      values[evenIndex] = values[oddIndex];
      values[oddIndex] = value;
    }
  }
  return values;
}
class Solution {
  sortArrayByParityII(nums) {
    return arrangeParity(nums);
  }
}
