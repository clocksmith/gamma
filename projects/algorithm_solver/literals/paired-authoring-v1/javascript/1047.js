class Solution {
  removeDuplicates(s) {
    const stack = [];
    for (const character of s) {
      if (stack.length > 0 && stack[stack.length - 1] === character) {
        stack.pop();
      } else {
        stack.push(character);
      }
    }
    return stack.join("");
  }
}
