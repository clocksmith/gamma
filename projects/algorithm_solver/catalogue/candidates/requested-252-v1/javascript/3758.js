/**
 * 3758. Convert Number Words to Digits
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(s).
 * Algorithm: Scan left to right for one of ten bounded-length words, consuming an entire matched word.
 * Complexity: O(n) time; O(n) output space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/convert-number-words-to-digits/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3758.Convert%20Number%20Words%20to%20Digits/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(s) {
  const words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
  const digits = [];
  let index = 0;
  while (index < s.length) {
    let matched = false;
    for (let digit = 0; digit < words.length; digit += 1) {
      if (s.startsWith(words[digit], index)) {
        digits.push(String(digit));
        index += words[digit].length;
        matched = true;
        break;
      }
    }
    if (!matched) index += 1;
  }
  return digits.join("");
}

function convertNumber(s) {
  return solve(s);
}

class Solution {
  convertNumber(s) {
    return solve(s);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, convertNumber, Solution };
}
