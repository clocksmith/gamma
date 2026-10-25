class Solution {
  gcdOfStrings(str1, str2) {
    let first = str1.length;
    let second = str2.length;
    while (second !== 0) {
      [first, second] = [second, first % second];
    }
    const period = first;
    for (let index = 0; index < str1.length; index += 1) {
      if (str1[index] !== str1[index % period]) {
        return "";
      }
    }
    for (let index = 0; index < str2.length; index += 1) {
      if (str2[index] !== str1[index % period]) {
        return "";
      }
    }
    return str1.slice(0, period);
  }
}
