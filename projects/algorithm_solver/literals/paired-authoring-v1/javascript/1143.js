class Solution {
  longestCommonSubsequence(text1, text2) {
    if (text1.length === 0 || text2.length === 0) {
      return 0;
    }
    if (text1.length < text2.length) {
      [text1, text2] = [text2, text1];
    }
    const lengths = Array(text2.length + 1).fill(0);
    for (const first of text1) {
      let diagonal = 0;
      for (let index = 1; index <= text2.length; index += 1) {
        const above = lengths[index];
        if (first === text2[index - 1]) {
          lengths[index] = diagonal + 1;
        } else {
          lengths[index] = Math.max(lengths[index], lengths[index - 1]);
        }
        diagonal = above;
      }
    }
    return lengths[lengths.length - 1];
  }
}
