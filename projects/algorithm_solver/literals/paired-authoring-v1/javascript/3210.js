class Solution {
  getEncryptedString(s, k) {
    if (s.length === 0) {
      return "";
    }
    const shift = k % s.length;
    return s.slice(shift) + s.slice(0, shift);
  }
}
