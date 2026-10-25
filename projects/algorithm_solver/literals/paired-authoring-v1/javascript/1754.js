class Solution {
  largestMerge(word1, word2) {
    let first = 0;
    let second = 0;
    const output = [];
    while (first < word1.length && second < word2.length) {
      if (word1.slice(first) > word2.slice(second)) {
        output.push(word1[first]);
        first += 1;
      } else {
        output.push(word2[second]);
        second += 1;
      }
    }
    output.push(word1.slice(first));
    output.push(word2.slice(second));
    return output.join("");
  }
}
