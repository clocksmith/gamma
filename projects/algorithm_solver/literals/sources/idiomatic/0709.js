class Solution {
  toLowerCase(values) {
    return values.replace(/[A-Z]/g, value => value.toLowerCase());
  }
}
