class Solution {
  breakPalindrome(palindrome) {
    if (palindrome.length <= 1) {
      return "";
    }
    for (let index = 0; index < Math.floor(palindrome.length / 2); index += 1) {
      if (palindrome[index] !== "a") {
        return palindrome.slice(0, index) + "a" + palindrome.slice(index + 1);
      }
    }
    return palindrome.slice(0, -1) + "b";
  }
}
