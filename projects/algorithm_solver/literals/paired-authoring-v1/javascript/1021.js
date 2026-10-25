class Solution {
  removeOuterParentheses(s) {
    let depth = 0;
    const output = [];
    for (const character of s) {
      if (character === "(") {
        if (depth > 0) {
          output.push(character);
        }
        depth += 1;
      } else {
        depth -= 1;
        if (depth > 0) {
          output.push(character);
        }
      }
    }
    return output.join("");
  }
}
