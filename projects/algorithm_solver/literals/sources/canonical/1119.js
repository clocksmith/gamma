class Solution {
  removeVowels(values) {
    let result = '';
    for (const value of values) {
      if (!'aeiou'.includes(value)) {
        result += value;
      }
    }
    return result;
  }
}
