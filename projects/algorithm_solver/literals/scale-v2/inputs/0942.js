function constructPermutation(text) {
  let minimumValue = 0;
  let maximumValue = Array.from(text).length;
  const resultValues = [];
  for (const character of text) {
    if (character === 'I') {
      resultValues.push(minimumValue);
      minimumValue += 1;
    } else {
      resultValues.push(maximumValue);
      maximumValue -= 1;
    }
  }
  resultValues.push(minimumValue);
  return resultValues;
}
class Solution {
  diStringMatch(s) {
    return constructPermutation(s);
  }
}
