class Solution {
  defangIPaddr(address) {
    const result = [];
    for (const character of address) {
      if (character === ".") {
        result.push("[.]");
      } else {
        result.push(character);
      }
    }
    return result.join("");
  }
}
