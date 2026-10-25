class Solution {
  finalString(s) {
    const left = [];
    const right = [];
    let reversedOrder = false;
    for (const character of s) {
      if (character === "i") {
        reversedOrder = !reversedOrder;
      } else if (reversedOrder) {
        left.push(character);
      } else {
        right.push(character);
      }
    }
    if (reversedOrder) {
      right.reverse();
      return right.join("") + left.join("");
    }
    left.reverse();
    return left.join("") + right.join("");
  }
}
