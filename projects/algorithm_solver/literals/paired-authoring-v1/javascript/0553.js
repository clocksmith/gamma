class Solution {
  optimalDivision(nums) {
    const terms = [];
    for (const value of nums) {
      terms.push(String(value));
    }
    if (terms.length === 1) {
      return terms[0];
    }
    if (terms.length === 2) {
      return terms[0] + "/" + terms[1];
    }
    return terms[0] + "/(" + terms.slice(1).join("/") + ")";
  }
}
