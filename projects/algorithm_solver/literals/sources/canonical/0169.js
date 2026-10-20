class Solution {
  majorityElement(values) {
    let result = 0;
    let count = 0;
    for (const value of values) {
      if (count === 0) {
        result = value;
      }
      if (value === result) {
        count += 1;
      } else {
        count -= 1;
      }
    }
    return result;
  }
}
